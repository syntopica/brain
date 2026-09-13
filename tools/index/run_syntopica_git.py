"""Bounded, local Git inspection independent of ambient repository settings."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


def run_syntopica_git(root: Path, arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    """Inspect a selected checkout without global configuration or inherited GIT_DIR."""
    try:
        return subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
            env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        raise InvalidSyntopicaConfigError("Cannot inspect configured Git repository") from None
