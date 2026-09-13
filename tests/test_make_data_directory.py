"""A portable, synthetic instance that never copies private wiki data."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.syntopica_git import syntopica_git
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.syntopica_config_schema import SYNTOPICA_CONFIG_SCHEMA
from tools.index.validate_syntopica_schema import validate_syntopica_schema


def test_fixture_config_validates_and_loads(tmp_path: Path) -> None:
    root = make_data_directory(tmp_path)
    document = json.loads((root / "syntopica.config.json").read_text(encoding="utf-8"))
    validate_syntopica_schema(document, SYNTOPICA_CONFIG_SCHEMA)
    config = load_syntopica_config(root, {})
    assert root.is_relative_to(tmp_path)
    assert config.index == root / "brain/index.md"
    assert config.index.is_file()
    assert (root / "mem").is_dir()
    roots = (root, config.archive, config.brain_path, config.clips_path)
    assert len(set(roots)) == 4
    for repository in roots:
        assert (
            Path(syntopica_git(repository, "rev-parse", "--show-toplevel").stdout.strip())
            == repository
        )


def test_fixture_preserves_pages_and_indexes_every_one(tmp_path: Path) -> None:
    pages = {"notes/a.md": "Generic note.\n", "projects/b.md": "Generic project.\n"}
    root = make_data_directory(tmp_path, pages)
    index = (root / "brain/index.md").read_text(encoding="utf-8")
    for name, content in pages.items():
        assert (root / "brain" / name).read_text(encoding="utf-8") == content
        assert f"[[{name.removesuffix('.md')}]]" in index


def test_fixture_accepts_an_explicitly_empty_wiki(tmp_path: Path) -> None:
    root = make_data_directory(tmp_path, {})
    assert list((root / "brain").rglob("*.md")) == [root / "brain/index.md"]


def test_fixture_contains_no_personal_data(tmp_path: Path) -> None:
    make_data_directory(tmp_path)
    configured = os.environ.get("SYNTOPICA_PERSONAL_DATA_PATTERNS")
    if configured is None:
        pytest.skip("Set SYNTOPICA_PERSONAL_DATA_PATTERNS to run the private audit scan")
    patterns = Path(configured)
    result = subprocess.run(
        ["rg", "--hidden", "--no-ignore", "-i", "-l", "-f", str(patterns), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, "Private-pattern scan failed or matched fixture files"


def test_fixture_contains_no_home_path_or_email(tmp_path: Path) -> None:
    make_data_directory(tmp_path)
    broad = subprocess.run(
        [
            "rg",
            "--hidden",
            "--no-ignore",
            "-l",
            "-e",
            r"/Users/|/home/|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert broad.returncode == 1, "Broad privacy scan failed or matched fixture files"


@pytest.mark.parametrize("name", ["../escape.md", "/absolute.md", "index.md", "notes/page.txt"])
def test_fixture_rejects_invalid_page_paths(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="relative Markdown"):
        make_data_directory(tmp_path, {name: "Generic content."})
    assert not (tmp_path / "escape.md").exists()
