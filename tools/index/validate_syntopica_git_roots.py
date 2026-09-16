"""Verify archive containment and data/engine repository separation."""

from __future__ import annotations

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.run_syntopica_git import run_syntopica_git
from tools.index.validate_syntopica_git_remotes import validate_syntopica_git_remotes


def validate_syntopica_git_roots(roots: tuple[Path, ...]) -> None:
    """Keep the archive in data and require independent engine repositories.

    ``roots[0]`` is the data directory, ``roots[1]`` the archive, and the rest
    the engine checkouts the instance declares; a brain-only instance declares
    one.
    """
    if len(roots) < 3:
        raise InvalidSyntopicaConfigError("An instance must declare at least one engine")
    archive = roots[1].resolve()
    if not archive.is_dir() or not archive.is_relative_to(roots[0]):
        raise InvalidSyntopicaConfigError(
            "Archive must be an existing directory within the data directory"
        )
    repositories = (roots[0], *roots[2:])
    if len(set(repositories)) != len(repositories):
        raise InvalidSyntopicaConfigError("Data and engines must have distinct Git roots")
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
        raise InvalidSyntopicaConfigError("Data and engines must have distinct Git roots")
