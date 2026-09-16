"""Configuration precedence, path ownership and credential boundaries."""

from __future__ import annotations

import json
from collections import UserDict
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import cast

import pytest

from tests.syntopica_git import syntopica_git
from tests.syntopica_test_directory import syntopica_test_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.merge_config_overrides import merge_config_overrides


def _write(root: Path, document: object, filename: str = "syntopica.config.json") -> None:
    (root / filename).write_text(json.dumps(document), encoding="utf-8")


def _with_defaults(document: dict[str, object]) -> dict[str, object]:
    from tools.index.merge_syntopica_documents import merge_syntopica_documents
    from tools.index.syntopica_config_schema import SYNTOPICA_CONFIG_SCHEMA
    from tools.index.syntopica_schema_defaults import syntopica_schema_defaults

    return merge_syntopica_documents(syntopica_schema_defaults(SYNTOPICA_CONFIG_SCHEMA), document)


def _default_origins(root: Path) -> dict[tuple[str, ...], Path]:
    from tools.index.syntopica_value_origins import syntopica_value_origins

    return syntopica_value_origins(_with_defaults({}), root)


def test_valid_config_resolves_paths_from_its_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    monkeypatch.chdir(tmp_path)
    config = load_syntopica_config(root, {})
    assert config.schema_version == 1
    assert config.instance_id == "fixture"
    assert config.pages == (root / "brain/notes",)
    assert config.sources == root / "brain/captures"
    assert config.index == root / "brain/index.md"
    assert config.ledger == root / "brain/.ingest"
    assert config.archive == root / "clips"
    assert config.brain_path == tmp_path / "engine-brain"
    assert config.clips_path == tmp_path / "engine-clips"
    assert config.capture_origin is None and config.capture_mirror is False
    assert config.browser is None and set(config.runners.values()) == {None}
    with pytest.raises(FrozenInstanceError):
        config.__setattr__("instance_id", "changed")
    with pytest.raises(TypeError):
        cast(dict[str, str | None], config.runners)["grade"] = "cursor"


@pytest.mark.parametrize(
    "section,key,value",
    [
        (None, "unknown", True),
        (None, "instanceId", ""),
        (None, "schemaVersion", False),
        ("brain", "pages", ["../escape"]),
        ("brain", "pages", ["/absolute"]),
        ("capture", "origin", "https://user:secret@example.test"),
        ("capture", "origin", "https://example.test?token=secret"),
        ("runners", "grade", "shell command"),
        ("browser", "executable", 12),
    ],
)
def test_invalid_configuration_is_rejected(
    tmp_path: Path, section: str | None, key: str, value: object
) -> None:
    root, document = syntopica_test_directory(tmp_path)
    target = (
        document if section is None else cast(dict[str, object], document.setdefault(section, {}))
    )
    target[key] = value
    _write(root, document)
    with pytest.raises(InvalidSyntopicaConfigError):
        load_syntopica_config(root, {})


def test_symlink_page_cannot_escape(tmp_path: Path) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    (root / "brain").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(InvalidSyntopicaConfigError, match="escapes"):
        load_syntopica_config(root, {})


@pytest.mark.parametrize(
    "first,second",
    [
        ("data", "brain"),
        ("data", "clips"),
        ("archive", "brain"),
        ("archive", "clips"),
        ("brain", "clips"),
    ],
)
def test_engine_git_roots_must_differ(tmp_path: Path, first: str, second: str) -> None:
    root, document = syntopica_test_directory(tmp_path)
    paths = {
        "data": ".",
        "archive": "clips",
        "brain": "../engine-brain",
        "clips": "../engine-clips",
    }
    cast(dict[str, dict[str, object]], document["engines"])[second]["path"] = paths[first]
    _write(root, document)
    with pytest.raises(InvalidSyntopicaConfigError, match=r"distinct|Git worktree root"):
        load_syntopica_config(root, {})


def test_nested_path_is_not_a_distinct_git_root(tmp_path: Path) -> None:
    root, document = syntopica_test_directory(tmp_path)
    (root / "subdirectory").mkdir()
    cast(dict[str, dict[str, object]], document["engines"])["brain"]["path"] = "subdirectory"
    _write(root, document)
    with pytest.raises(InvalidSyntopicaConfigError):
        load_syntopica_config(root, {})


def test_symlink_engine_alias_is_not_a_distinct_root(tmp_path: Path) -> None:
    root, document = syntopica_test_directory(tmp_path)
    (root / "engine-alias").symlink_to(root, target_is_directory=True)
    cast(dict[str, dict[str, object]], document["engines"])["brain"]["path"] = "engine-alias"
    _write(root, document)
    with pytest.raises(InvalidSyntopicaConfigError):
        load_syntopica_config(root, {})


def test_missing_engine_is_rejected(tmp_path: Path) -> None:
    root, document = syntopica_test_directory(tmp_path)
    cast(dict[str, dict[str, object]], document["engines"])["brain"]["path"] = "absent"
    _write(root, document)
    with pytest.raises(InvalidSyntopicaConfigError):
        load_syntopica_config(root, {})


def test_precedence_defaults_tracked_local_environment(tmp_path: Path) -> None:
    root, document = syntopica_test_directory(tmp_path)
    assert load_syntopica_config(root, {}).capture_mirror is False
    document["capture"] = {"origin": "https://tracked.test", "mirror": True}
    document["runners"] = {"synthesis": "manual", "grade": "codex"}
    _write(root, document)
    assert load_syntopica_config(root, {}).capture_mirror is True
    _write(
        root,
        {"capture": {"mirror": False}, "runners": {"grade": "agy-fine"}},
        "syntopica.local.json",
    )
    local = load_syntopica_config(root, {})
    assert local.capture_mirror is False and local.capture_origin == "https://tracked.test"
    assert local.runners["grade"] == "agy-fine" and local.runners["synthesis"] == "manual"
    config = load_syntopica_config(
        root,
        {
            "SYNTOPICA_DATA": "/ignored",
            "CAPTURE_MIRROR": "on",
            "CAPTURE_SERVICE_ORIGIN": "https://environment.test",
            "CLIPS_GRADE_RUNNER": "cursor",
            "CLIPS_SYNTHESIS_RUNNER": "codex",
            "CLIPS_TRIAGE_RUNNER": "agy-bulk",
            "CLIPS_TRIAGE_REFINER": "agy-fine",
            "CLIPS_HEADLESS_BROWSER": "/browser",
        },
    )
    assert config.capture_mirror is True and config.capture_origin == "https://environment.test"
    assert dict(config.runners) == {
        "grade": "cursor",
        "synthesis": "codex",
        "triage": "agy-bulk",
        "triageRefiner": "agy-fine",
    }
    assert config.browser == "/browser" and config.pages[0].is_relative_to(root)
    assert load_syntopica_config(root, {"CAPTURE_MIRROR": "off"}).capture_mirror is False


@pytest.mark.parametrize(
    "environment",
    [
        {"CAPTURE_MIRROR": "true"},
        {"CAPTURE_MIRROR": ""},
        {"CAPTURE_MIRROR": "ON"},
        {"CLIPS_GRADE_RUNNER": "arbitrary"},
        {"CAPTURE_SERVICE_ORIGIN": "https://example.test/path"},
    ],
)
def test_environment_overrides_are_validated(tmp_path: Path, environment: dict[str, str]) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    with pytest.raises(InvalidSyntopicaConfigError):
        load_syntopica_config(root, environment)


def test_overrides_do_not_mutate_the_input() -> None:
    original: dict[str, object] = {"capture": {"mirror": False}}
    merged = merge_config_overrides(original, {"CAPTURE_MIRROR": "on"})
    assert original == {"capture": {"mirror": False}}
    assert merged == {"capture": {"mirror": True}}


def test_capture_token_is_never_read_or_returned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    class CredentialGuard(UserDict[str, str]):
        def __getitem__(self, key: str) -> str:
            assert key != "CAPTURE_TOKEN"
            return super().__getitem__(key)

    root, _ = syntopica_test_directory(tmp_path)
    config = load_syntopica_config(root, CredentialGuard({"CAPTURE_TOKEN": "synthetic-secret"}))
    assert "synthetic-secret" not in repr(config)
    assert not any("token" in field.name.lower() for field in fields(config))
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "url",
    [
        "https://user:synthetic-secret@example.test/repo",
        "https://synthetic-secret@example.test/repo",
        "https://example.test/repo?token=synthetic-secret",
        "https://example.test/repo?X-Amz-Signature=synthetic-secret",
    ],
)
@pytest.mark.parametrize("repository", ["data", "archive", "brain", "clips"])
def test_credentialed_git_remotes_are_rejected(
    tmp_path: Path, url: str, repository: str, capsys: pytest.CaptureFixture[str]
) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    paths = {
        "data": root,
        "archive": root / "clips",
        "brain": tmp_path / "engine-brain",
        "clips": tmp_path / "engine-clips",
    }
    syntopica_git(paths[repository], "config", "remote.origin.url", url)
    with pytest.raises(InvalidSyntopicaConfigError) as error:
        load_syntopica_config(root, {})
    assert "synthetic-secret" not in str(error.value)
    assert capsys.readouterr() == ("", "")


def test_safe_https_and_ssh_remotes_are_accepted(tmp_path: Path) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    syntopica_git(root, "config", "remote.origin.url", "https://example.test/repo.git")
    syntopica_git(root, "config", "remote.origin.pushurl", "git@example.test:repo.git")
    load_syntopica_config(root, {})


def test_local_paths_follow_the_defining_file(tmp_path: Path) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    machine = tmp_path / "machine"
    machine.mkdir()
    override = machine / "local.json"
    override.write_text(
        json.dumps(
            {
                "engines": {"brain": {"path": "../engine-brain"}},
                "browser": {"executable": "browser"},
            }
        )
    )
    (root / "syntopica.local.json").symlink_to(override)
    config = load_syntopica_config(root, {})
    assert config.brain_path == tmp_path / "engine-brain"
    assert config.clips_path == tmp_path / "engine-clips"
    assert config.pages == (root / "brain/notes",)


@pytest.mark.parametrize(
    "text",
    ["[]", "null", "{", '{"schemaVersion": 1, "schemaVersion": 2}', '{"schemaVersion": NaN}'],
)
def test_invalid_json_is_a_config_error(tmp_path: Path, text: str) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    (root / "syntopica.config.json").write_text(text, encoding="utf-8")
    with pytest.raises(InvalidSyntopicaConfigError):
        load_syntopica_config(root, {})


def test_both_engines_cannot_be_the_data_root(tmp_path: Path) -> None:
    root, document = syntopica_test_directory(tmp_path)
    document["engines"] = {
        "brain": {"path": ".", "apiVersion": 1},
        "clips": {"path": ".", "apiVersion": 1},
    }
    _write(root, document)
    with pytest.raises(InvalidSyntopicaConfigError, match="distinct Git roots"):
        load_syntopica_config(root, {})


@pytest.mark.parametrize("archive", [".", "clips"])
def test_archive_can_share_data_root(tmp_path: Path, archive: str) -> None:
    root, document = syntopica_test_directory(tmp_path)
    document["clips"] = {"archive": archive}
    _write(root, document)
    assert load_syntopica_config(root, {}).archive == (root / archive).resolve()


def test_optional_engines_resolve_when_present_and_are_empty_when_absent(
    tmp_path: Path,
) -> None:
    from tools.index.resolve_syntopica_paths import resolve_syntopica_paths

    root, document = syntopica_test_directory(tmp_path)
    (tmp_path / "engine-atrium").mkdir()
    engines = cast(dict[str, object], document["engines"])
    engines["atrium"] = {"path": "../engine-atrium", "apiVersion": 1}
    engines.pop("clips")
    origins: dict[tuple[str, ...], Path] = {
        ("engines", "brain", "path"): root,
        ("engines", "atrium", "path"): root,
        ("brain", "pages"): root,
        ("brain", "sources"): root,
        ("brain", "index"): root,
        ("brain", "ledger"): root,
    }
    paths = resolve_syntopica_paths(
        _with_defaults(document), _default_origins(root) | origins, root
    )
    assert paths[("engines", "atrium", "path")] == (tmp_path / "engine-atrium",)
    assert paths[("engines", "clips", "path")] == ()
    assert paths[("engines", "agents", "path")] == ()


def test_brain_only_instance_loads_without_a_clips_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, document = syntopica_test_directory(tmp_path)
    cast(dict[str, object], document["engines"]).pop("clips")
    _write(root, document)
    monkeypatch.chdir(tmp_path)
    config = load_syntopica_config(root, {})
    assert config.clips_path is None
    assert config.clips_api_version is None
    assert config.brain_path == tmp_path / "engine-brain"
