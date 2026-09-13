"""Choose the archive without turning the temporary monorepo into a cutover."""

import os
from pathlib import Path

from tools.index.syntopica_config import SyntopicaConfig


def configured_archive(config: SyntopicaConfig, explicit: bool = False) -> Path:
    """Use the legacy archive only for an implicitly selected monorepo."""
    if (
        not explicit
        and "SYNTOPICA_DATA" not in os.environ
        and config.data_root == config.brain_path == config.clips_path == config.archive
        and config.legacy_archive is not None
    ):
        return config.legacy_archive
    return config.archive
