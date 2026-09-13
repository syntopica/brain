"""Git commands confined to synthetic test repositories."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def syntopica_git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run local Git without the developer's global configuration."""
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
    )
