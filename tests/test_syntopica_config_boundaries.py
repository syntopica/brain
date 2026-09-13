"""Regressions for file provenance and indirect remote credentials."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.syntopica_git import syntopica_git
from tests.syntopica_test_directory import syntopica_test_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config


@pytest.mark.parametrize("rewrite", ["insteadOf", "pushInsteadOf"])
def test_authenticated_remote_rewrite_is_rejected(tmp_path: Path, rewrite: str) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    syntopica_git(root, "config", "remote.origin.url", "review:repo.git")
    syntopica_git(
        root, "config", f"url.https://synthetic-secret@example.test/.{rewrite}", "review:"
    )
    with pytest.raises(InvalidSyntopicaConfigError) as error:
        load_syntopica_config(root, {})
    assert "synthetic-secret" not in str(error.value)


def test_relative_browser_uses_local_file_directory(tmp_path: Path) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    machine = tmp_path / "machine"
    machine.mkdir()
    (machine / "local.json").write_text(json.dumps({"browser": {"executable": "./bin/browser"}}))
    (root / "syntopica.local.json").symlink_to(machine / "local.json")
    assert load_syntopica_config(root, {}).browser == str(machine / "bin/browser")


def test_browser_environment_path_uses_selected_root(tmp_path: Path) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    config = load_syntopica_config(root, {"CLIPS_HEADLESS_BROWSER": "./browser"})
    assert config.browser == str(root / "browser")


def test_bare_browser_command_is_preserved(tmp_path: Path) -> None:
    root, _ = syntopica_test_directory(tmp_path)
    assert load_syntopica_config(root, {"CLIPS_HEADLESS_BROWSER": "chromium"}).browser == "chromium"
