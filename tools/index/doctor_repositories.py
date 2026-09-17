"""Check worktree and common-directory separation."""

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.syntopica_config import SyntopicaConfig
from tools.index.validate_syntopica_git_roots import validate_syntopica_git_roots


def doctor_repositories(root: Path, config: SyntopicaConfig) -> tuple[bool, str]:
    """Require independent data and engine repository identities."""
    engines = tuple(path for path in (config.brain_path, config.clips_path) if path is not None)
    try:
        validate_syntopica_git_roots(root.resolve(), config.archive, engines)
    except InvalidSyntopicaConfigError:
        return False, "repositories: invalid Git identities or remotes"
    return True, "repositories: valid Git identities"
