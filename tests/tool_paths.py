"""Every Python tool this repository maintains, as paths.

One place decides what "a tool" is, so a test never disagrees with the
configuration: `tools/` is the live tooling, `sources/vault` is archived
material that no test speaks for, and an untracked file is scratch - somebody
mid-experiment, not code this repository has adopted.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_ROOT = ROOT / "tools"


def tool_paths() -> list[Path]:
    """Return every tracked tool file, sorted, so failures name a stable case."""
    tracked = subprocess.run(
        ["git", "ls-files", "tools"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return sorted(
        ROOT / name for name in tracked if name.endswith(".py") and "__pycache__" not in name
    )
