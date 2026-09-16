"""Archive containment and data/engine Git separation regressions."""

from pathlib import Path

import pytest

from tests.syntopica_git import syntopica_git
from tests.syntopica_test_directory import syntopica_test_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.validate_syntopica_git_roots import validate_syntopica_git_roots


@pytest.mark.parametrize("archive", ["clips", "."])
def test_archive_can_share_data_repository(tmp_path: Path, archive: str) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    brain = tmp_path / "engine-brain"
    clips = tmp_path / "engine-clips"
    assert not (data / "clips" / ".git").exists()
    validate_syntopica_git_roots((data, data / archive, brain, clips))


@pytest.mark.parametrize("engine", ["brain", "clips"])
@pytest.mark.parametrize("location", [".", "clips"])
def test_engine_cannot_share_data_worktree(tmp_path: Path, engine: str, location: str) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    brain = data / location if engine == "brain" else tmp_path / "engine-brain"
    clips = data / location if engine == "clips" else tmp_path / "engine-clips"
    with pytest.raises(InvalidSyntopicaConfigError):
        validate_syntopica_git_roots((data, data / "clips", brain, clips))


def test_engines_cannot_share_root(tmp_path: Path) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    brain = tmp_path / "engine-brain"
    with pytest.raises(InvalidSyntopicaConfigError, match="distinct Git roots"):
        validate_syntopica_git_roots((data, data / "clips", brain, brain))


@pytest.mark.parametrize("location", ["missing", "file", "outside", "symlink"])
def test_archive_must_be_existing_contained_directory(tmp_path: Path, location: str) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    outside = tmp_path / "data-other"
    outside.mkdir()
    (data / "file").write_text("fixture")
    (data / "symlink").symlink_to(outside, target_is_directory=True)
    archive = outside if location == "outside" else data / location
    brain = tmp_path / "engine-brain"
    clips = tmp_path / "engine-clips"
    with pytest.raises(InvalidSyntopicaConfigError, match="Archive"):
        validate_syntopica_git_roots((data, archive, brain, clips))


@pytest.mark.parametrize("owner", ["data", "engine-brain"])
def test_engine_cannot_share_git_common_directory(tmp_path: Path, owner: str) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    repository = tmp_path / owner
    worktree = tmp_path / "engine-worktree"
    syntopica_git(
        repository,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.test",
        "commit",
        "--allow-empty",
        "-m",
        "Fixture",
    )
    syntopica_git(repository, "worktree", "add", "--detach", str(worktree))
    with pytest.raises(InvalidSyntopicaConfigError, match="distinct Git roots"):
        validate_syntopica_git_roots((data, data / "clips", tmp_path / "engine-brain", worktree))


def test_engines_cannot_both_share_data_repository(tmp_path: Path) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    with pytest.raises(InvalidSyntopicaConfigError, match="distinct Git roots"):
        validate_syntopica_git_roots((data, data / "clips", data, data))


def test_a_single_engine_root_is_enough(tmp_path: Path) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    validate_syntopica_git_roots((data, data / "clips", tmp_path / "engine-brain"))


def test_no_engine_root_is_rejected(tmp_path: Path) -> None:
    data, _ = syntopica_test_directory(tmp_path)
    with pytest.raises(InvalidSyntopicaConfigError, match="at least one engine"):
        validate_syntopica_git_roots((data, data / "clips"))
