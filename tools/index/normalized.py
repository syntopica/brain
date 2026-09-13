"""Normalized: extracted from build.py."""

import re


def normalized(text: str) -> str:
    """Return the content, ignoring every line break.

    The generator emits one bullet per
    line and prettier then wraps them at 80 columns, so a byte comparison would
    call the map stale the moment `pnpm run check` ran - a check that always
    fires, which is the failure mode this repo has already switched one check
    off for.

    Collapsing all whitespace is safe here because every item starts with an
    unambiguous marker (`- [[`, `## `, `#`), so two entries cannot merge into
    one without the text of one of them changing as well.
    """
    return re.sub(r"\s+", " ", text).strip()
