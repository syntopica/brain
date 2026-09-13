"""Check required runtimes and explicitly enabled integrations."""

import os
import shutil
from collections.abc import Mapping

from tools.index.syntopica_config import SyntopicaConfig


def doctor_executables(config: SyntopicaConfig, environ: Mapping[str, str]) -> tuple[bool, str]:
    """Resolve commands on the supplied PATH without executing integrations."""
    commands = {"git", "uv", "node", "pnpm"}
    adapters = {"codex": "codex", "agy-fine": "agy", "agy-bulk": "agy", "cursor": "cursor-agent"}
    commands.update(adapters[runner] for runner in config.runners.values() if runner in adapters)
    if config.browser is not None:
        commands.add(config.browser)
    missing = sum(
        shutil.which(command, path=environ.get("PATH", os.defpath)) is None for command in commands
    )
    return missing == 0, f"executables: {missing} missing"
