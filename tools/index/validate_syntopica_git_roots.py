"""Verify archive containment and data/engine repository separation."""

from __future__ import annotations

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.run_syntopica_git import run_syntopica_git
from tools.index.validate_syntopica_git_remotes import validate_syntopica_git_remotes


def validate_syntopica_git_roots(
    data_root: Path, archive: Path | None, engines: tuple[Path, ...]
) -> None:
    """Keep the archive in data and require independent engine repositories.

    ``archive`` is ``None`` for an instance that declares no clips engine: the
    archive is where captured clips land, so requiring the directory of a
    component the instance does not have turned a brain-only setup into a
    configuration error.
    """
    if not engines:
        raise InvalidSyntopicaConfigError("An instance must declare at least one engine")
    if archive is not None:
        resolved = archive.resolve()
        if not resolved.is_dir() or not resolved.is_relative_to(data_root):
            raise InvalidSyntopicaConfigError(
                "Archive must be an existing directory within the data directory"
            )
    repositories = (data_root, *engines)
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
