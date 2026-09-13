"""Check worktree and common-directory separation."""

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.syntopica_config import SyntopicaConfig
from tools.index.validate_syntopica_git_roots import validate_syntopica_git_roots


def doctor_repositories(root: Path, config: SyntopicaConfig) -> tuple[bool, str]:
    """Reuse the contract's exact temporary monorepo exception."""
    try:
        validate_syntopica_git_roots(
            (root.resolve(), config.archive, config.brain_path, config.clips_path)
        )
    except InvalidSyntopicaConfigError:
        return False, "repositories: invalid Git identities or remotes"
    return True, "repositories: valid Git identities"
