"""Doctor diagnoses synthetic installations without revealing credentials."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.syntopica_git import syntopica_git
from tools.index.doctor_report import doctor_report


def test_healthy_instance(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = make_data_directory(tmp_path)
    with patch("tools.index.doctor_executables.shutil.which", return_value="/synthetic/bin/tool"):
        assert doctor_report(root, {}) == 0
    assert len(capsys.readouterr().out.splitlines()) == 7


@pytest.mark.parametrize(
    "remote", ["https://github.com/syntopica/clips.git", "git@github.com:syntopica/brain.git"]
)
@pytest.mark.parametrize("setting", ["url", "pushurl"])
def test_public_archive_is_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], remote: str, setting: str
) -> None:
    root = make_data_directory(tmp_path)
    syntopica_git(root / "clips", "config", f"remote.origin.{setting}", remote)
    assert doctor_report(root, {}) == 1
    output = capsys.readouterr()
    assert "FAIL archive" in output.out
    assert remote not in output.out + output.err


def test_rewritten_public_archive_is_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    syntopica_git(root / "clips", "config", "remote.origin.url", "https://example.test/private")
    syntopica_git(
        root / "clips",
        "config",
        "url.https://github.com/syntopica/clips.git.pushInsteadOf",
        "https://example.test/private",
    )
    assert doctor_report(root, {}) == 1
    assert "FAIL archive" in capsys.readouterr().out


@pytest.mark.parametrize("token", ["distinctive-doctor-token-never-print-82713", ""])
def test_capture_token_presence_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], token: str
) -> None:
    root = make_data_directory(tmp_path)
    with patch("tools.index.doctor_executables.shutil.which", return_value="/synthetic/bin/tool"):
        assert doctor_report(
            root, {"CAPTURE_SERVICE_ORIGIN": "https://capture.example.test", "CAPTURE_TOKEN": token}
        ) == (0 if token else 1)
    output = capsys.readouterr()
    assert f"CAPTURE_TOKEN {'present' if token else 'absent'}" in output.out
    assert "distinctive-doctor-token-never-print-82713" not in output.out + output.err


def test_missing_optional_path_and_unsupported_api(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    (root / ".config/project-aliases.json").unlink()
    (root / "syntopica.local.json").write_text(
        json.dumps({"engines": {"clips": {"apiVersion": 2}}})
    )
    assert doctor_report(root, {}) == 1
    output = capsys.readouterr().out
    assert "FAIL paths" in output and "FAIL api" in output


def test_invalid_config_is_reported_without_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    (root / "syntopica.local.json").write_text(
        '{"unexpected": "distinctive-doctor-token-never-print-82713"}'
    )
    assert doctor_report(root, {}) == 1
    output = capsys.readouterr()
    assert "FAIL configuration" in output.out
    assert "distinctive-doctor-token-never-print-82713" not in output.out + output.err


def test_missing_enabled_runner_and_browser(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    assert (
        doctor_report(
            root,
            {
                "PATH": os.defpath,
                "CLIPS_GRADE_RUNNER": "cursor",
                "CLIPS_HEADLESS_BROWSER": "/absent/browser",
            },
        )
        == 1
    )
    assert "FAIL executables" in capsys.readouterr().out


def test_shared_git_roots_explain_the_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    (root / "syntopica.local.json").write_text(json.dumps({"engines": {"brain": {"path": "."}}}))
    assert doctor_report(root, {}) == 1
    assert "distinct Git roots" in capsys.readouterr().out


def test_both_engines_sharing_data_are_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    (root / "syntopica.local.json").write_text(
        json.dumps({"engines": {"brain": {"path": "."}, "clips": {"path": "."}}})
    )
    assert doctor_report(root, {}) == 1
    assert "distinct Git roots" in capsys.readouterr().out


@pytest.mark.parametrize(
    "remote",
    [
        "https://github.com/Syntopica/Clips.GIT/",
        "ssh://git@github.com/syntopica/brain.git",
        "git://github.com/syntopica/clips",
        "https://github.com/%73yntopica/clips",
    ],
)
def test_public_remote_url_forms(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], remote: str
) -> None:
    root = make_data_directory(tmp_path)
    syntopica_git(root / "clips", "config", "remote.origin.url", remote)
    assert doctor_report(root, {}) == 1
    assert "FAIL archive" in capsys.readouterr().out


def test_raw_public_url_cannot_hide_behind_rewrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    syntopica_git(
        root / "clips", "config", "remote.origin.url", "https://github.com/syntopica/clips.git"
    )
    syntopica_git(
        root / "clips",
        "config",
        "url.https://example.test/private.insteadOf",
        "https://github.com/syntopica/clips.git",
    )
    assert doctor_report(root, {}) == 1
    assert "FAIL archive" in capsys.readouterr().out
