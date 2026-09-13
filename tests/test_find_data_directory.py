"""Explicit selection, environment selection and bounded upward discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.index.data_directory_not_found_error import DataDirectoryNotFoundError
from tools.index.find_data_directory import find_data_directory


def _make(tmp_path: Path, name: str = "data") -> Path:
    root = tmp_path / name
    (root / ".git").mkdir(parents=True)
    (root / "syntopica.config.json").write_text("{}", encoding="utf-8")
    return root


def test_explicit_path_wins(tmp_path: Path) -> None:
    chosen, other = _make(tmp_path, "a"), _make(tmp_path, "b")
    assert find_data_directory(str(chosen), {"SYNTOPICA_DATA": str(other)}, other) == chosen


def test_invalid_explicit_path_is_an_error_not_a_fallthrough(tmp_path: Path) -> None:
    fallback = _make(tmp_path)
    with pytest.raises(DataDirectoryNotFoundError):
        find_data_directory(str(tmp_path / "nope"), {"SYNTOPICA_DATA": str(fallback)}, fallback)


def test_environment_beats_the_walk(tmp_path: Path) -> None:
    chosen, walked = _make(tmp_path, "a"), _make(tmp_path, "b")
    assert find_data_directory(None, {"SYNTOPICA_DATA": str(chosen)}, walked) == chosen


def test_walk_upward_from_the_caller(tmp_path: Path) -> None:
    root = _make(tmp_path)
    deep = root / "brain" / "notes"
    deep.mkdir(parents=True)
    assert find_data_directory(None, {}, deep) == root


def test_the_walk_stops_at_the_git_root(tmp_path: Path) -> None:
    outer = _make(tmp_path, "outer")
    inner = outer / "inner"
    (inner / ".git").mkdir(parents=True)
    with pytest.raises(DataDirectoryNotFoundError):
        find_data_directory(None, {}, inner)


def test_failure_names_what_was_searched(tmp_path: Path) -> None:
    with pytest.raises(DataDirectoryNotFoundError, match=r"syntopica\.config\.json") as error:
        find_data_directory(None, {}, tmp_path)
    assert str(tmp_path) in str(error.value)


@pytest.mark.parametrize("explicit", [True, False])
def test_existing_invalid_candidate_never_falls_through(tmp_path: Path, explicit: bool) -> None:
    fallback = _make(tmp_path)
    invalid = tmp_path / "empty"
    invalid.mkdir()
    with pytest.raises(DataDirectoryNotFoundError):
        find_data_directory(
            str(invalid) if explicit else None, {"SYNTOPICA_DATA": str(invalid)}, fallback
        )


def test_invalid_environment_path_never_falls_through(tmp_path: Path) -> None:
    fallback = _make(tmp_path)
    with pytest.raises(DataDirectoryNotFoundError):
        find_data_directory(None, {"SYNTOPICA_DATA": str(tmp_path / "absent")}, fallback)


def test_git_file_is_a_walk_boundary(tmp_path: Path) -> None:
    outer = _make(tmp_path)
    inner = outer / "worktree"
    inner.mkdir()
    (inner / ".git").write_text("gitdir: unused", encoding="utf-8")
    with pytest.raises(DataDirectoryNotFoundError):
        find_data_directory(None, {}, inner)
    (inner / "syntopica.config.json").write_text("{}", encoding="utf-8")
    assert find_data_directory(None, {}, inner) == inner


def test_relative_and_symlink_selections_are_resolved(tmp_path: Path) -> None:
    root = _make(tmp_path)
    (tmp_path / "alias").symlink_to(root, target_is_directory=True)
    assert find_data_directory("alias", {}, tmp_path) == root.resolve()
    assert find_data_directory(None, {"SYNTOPICA_DATA": "alias"}, tmp_path) == root.resolve()


def test_configuration_must_be_a_file(tmp_path: Path) -> None:
    (tmp_path / "syntopica.config.json").mkdir()
    with pytest.raises(DataDirectoryNotFoundError):
        find_data_directory(str(tmp_path), {}, tmp_path)
