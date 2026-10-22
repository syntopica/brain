"""Bounded Git inspection failures remain distinct and credential-free."""

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tools.index import doctor_checks as checks_module
from tools.index.doctor_document import doctor_document
from tools.index.doctor_repositories import doctor_repositories
from tools.index.git_inspection_timeout_error import GitInspectionTimeoutError
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.run_syntopica_git import run_syntopica_git


def test_configuration_timeout_has_an_operational_code() -> None:
    """The actual Git adapter must not mislabel its deadline as bad settings."""
    timeout = subprocess.TimeoutExpired(
        ["git", "synthetic-sensitive-command"],
        5,
        output="synthetic-sensitive-output",
        stderr="synthetic-sensitive-error",
    )
    with (
        patch("tools.index.run_syntopica_git.subprocess.run", side_effect=timeout) as run,
        patch(
            "tools.index.doctor_checks.load_syntopica_config",
            side_effect=lambda root, environ: run_syntopica_git(root, ("remote",)),
        ),
    ):
        document = doctor_document(Path("/synthetic/data"), {})
    assert document == {
        "schemaVersion": 1,
        "ok": False,
        "checks": [{"name": "configuration", "ok": False, "code": "git_inspection_timeout"}],
    }
    assert run.call_args.kwargs["timeout"] == 5
    assert "sensitive" not in str(document)


def test_timeout_is_safe_and_preserves_inspection_policy() -> None:
    timeout = subprocess.TimeoutExpired(
        ["synthetic-sensitive-command"], 5, output="sensitive-output", stderr="sensitive-error"
    )
    with (
        patch("tools.index.run_syntopica_git.subprocess.run", side_effect=timeout) as run,
        pytest.raises(GitInspectionTimeoutError) as caught,
    ):
        run_syntopica_git(Path("/synthetic/data"), ("remote",))
    assert isinstance(caught.value, InvalidSyntopicaConfigError)
    assert str(caught.value) == "Git inspection timed out"
    assert caught.value.__suppress_context__ is True
    assert run.call_args.kwargs["timeout"] == 5
    assert run.call_args.kwargs["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
    assert "GIT_DIR" not in run.call_args.kwargs["env"]
    assert run.call_args.args[0][1:3] == ["-c", "core.fsmonitor=false"]


def test_archive_timeout_preserves_earlier_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    config = SimpleNamespace(archive=Path("/synthetic/archive"))
    monkeypatch.setattr(checks_module, "load_syntopica_config", lambda root, environ: config)
    for name in ("paths", "repositories", "retrieval", "api", "executables", "credentials"):
        monkeypatch.setattr(
            checks_module, f"doctor_{name}", lambda *args: (True, "synthetic: valid", "ok")
        )
    with patch(
        "tools.index.run_syntopica_git.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["synthetic-sensitive-command"], 5),
    ):
        document = doctor_document(Path("/synthetic/data"), {})
    assert document["ok"] is False
    assert len(document["checks"]) == 8
    assert all(check["ok"] for check in document["checks"][:-1])
    assert document["checks"][-1] == {
        "name": "archive",
        "ok": False,
        "code": "git_inspection_timeout",
    }


def test_repository_recheck_timeout_has_an_operational_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = SimpleNamespace(archive=None, brain_path=Path("/synthetic/engine"), clips_path=None)
    monkeypatch.setattr(checks_module, "load_syntopica_config", lambda root, environ: config)
    for name in ("paths", "retrieval", "api", "executables", "credentials"):
        monkeypatch.setattr(
            checks_module, f"doctor_{name}", lambda *args: (True, "synthetic: valid", "ok")
        )
    with (
        patch(
            "tools.index.run_syntopica_git.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                ["synthetic-sensitive-command"], 5, output="sensitive", stderr="sensitive"
            ),
        ),
        patch(
            "tools.index.doctor_repositories.validate_syntopica_git_roots",
            side_effect=lambda root, archive, engines: run_syntopica_git(root, ("remote",)),
        ),
    ):
        document = doctor_document(Path("/synthetic/data"), {})
    assert document["ok"] is False
    assert [check for check in document["checks"] if not check["ok"]] == [
        {"name": "repositories", "ok": False, "code": "git_inspection_timeout"}
    ]
    assert "sensitive" not in str(document)


@pytest.mark.parametrize("failure", [OSError("synthetic-sensitive"), UnicodeError("sensitive")])
def test_other_inspection_failures_stay_invalid(failure: Exception) -> None:
    with (
        patch("tools.index.run_syntopica_git.subprocess.run", side_effect=failure),
        pytest.raises(InvalidSyntopicaConfigError) as caught,
    ):
        run_syntopica_git(Path("/synthetic/data"), ("remote",))
    assert type(caught.value) is InvalidSyntopicaConfigError
    assert str(caught.value) == "Cannot inspect configured Git repository"


def test_repository_identity_failure_keeps_its_code() -> None:
    config = SimpleNamespace(archive=None, brain_path=Path("/synthetic/engine"), clips_path=None)
    with patch(
        "tools.index.doctor_repositories.validate_syntopica_git_roots",
        side_effect=InvalidSyntopicaConfigError("synthetic-sensitive-identity"),
    ):
        result = doctor_repositories(Path("/synthetic/data"), config)
    assert result == (
        False,
        "repositories: invalid Git identities or remotes",
        "git_identity_invalid",
    )
