"""Verify the data, archive and engine repository separation."""

from __future__ import annotations

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.run_syntopica_git import run_syntopica_git
from tools.index.validate_syntopica_git_remotes import validate_syntopica_git_remotes


def validate_syntopica_git_roots(roots: tuple[Path, Path, Path, Path]) -> None:
    """Require distinct repositories, except for the temporary self-hosted monorepo."""
    # Phase 1 monorepo compatibility; removed when Phase 5 splits the engines.
    monorepo = roots[2] == roots[3] == roots[0]
    repositories = tuple(dict.fromkeys(roots)) if monorepo else roots
    if len(set(repositories)) != len(repositories):
        raise InvalidSyntopicaConfigError(
            "Data, archive and engines must have four distinct Git roots"
        )
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
        raise InvalidSyntopicaConfigError(
            "Data, archive and engines must have four distinct Git roots"
        )
