"""Verify archive containment and data/engine repository separation."""

from __future__ import annotations

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.run_syntopica_git import run_syntopica_git
from tools.index.validate_syntopica_git_remotes import validate_syntopica_git_remotes


def validate_syntopica_git_roots(roots: tuple[Path, Path, Path, Path]) -> None:
    """Keep the archive in data and require independent engine repositories."""
    archive = roots[1].resolve()
    if not archive.is_dir() or not archive.is_relative_to(roots[0]):
        raise InvalidSyntopicaConfigError(
            "Archive must be an existing directory within the data directory"
        )
    repositories = (roots[0], roots[2], roots[3])
    if len(set(repositories)) != len(repositories):
        raise InvalidSyntopicaConfigError("Data and engines must have three distinct Git roots")
    identities: set[Path] = set()
    for root in repositories:
        result = run_syntopica_git(root, ("rev-parse", "--show-toplevel", "--git-common-dir"))
        lines = result.stdout.splitlines()
        if result.returncode or len(lines) != 2 or Path(lines[0]).resolve() != root:
            raise InvalidSyntopicaConfigError(
                "Each configured repository must be a Git worktree root"
            )
        identities.add((root / lines[1]).resolve())
        validate_syntopica_git_remotes(root)
    if len(identities) != len(repositories):
        raise InvalidSyntopicaConfigError("Data and engines must have three distinct Git roots")
