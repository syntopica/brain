"""Where the Python configuration reader lives for a test that needs it.

The reader ships in the brain engine, so in the monorepo and in the brain
repository it is this checkout, while the clips repository reaches it through a
sibling checkout the way a real instance does. When there is no such sibling
there is no reader, and the tests that need one skip rather than lie.
"""

from pathlib import Path

READER = "tools/index/current_syntopica_config.py"
SIBLINGS = ("brain", "syntopica-brain", "engine-brain")


def brain_engine_path(root: Path) -> Path | None:
    """Return the checkout that provides the reader, or None when there is none."""
    candidates = [root, *(root.parent / name for name in SIBLINGS)]
    return next((path for path in candidates if (path / READER).is_file()), None)
