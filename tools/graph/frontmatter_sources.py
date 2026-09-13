"""The `sources:` entries a page's frontmatter lists, as a set."""

import re

ITEM = re.compile(r"^\s+-\s+(.+)$")


def frontmatter_sources(text: str) -> set[str]:
    """Every entry under the `sources:` key, or an empty set when there is none.

    A block list only, which is the shape SCHEMA.md defines; a page whose
    frontmatter is missing or unterminated carries no sources, and that is the
    honest answer rather than a parse error - the graph is a view, and one
    malformed page must not stop it being drawn.
    """
    if not text.startswith("---"):
        return set()
    end = text.find("\n---", 3)
    if end == -1:
        return set()
    sources: set[str] = set()
    collecting = False
    for line in text[3:end].splitlines():
        if line.rstrip() == "sources:":
            collecting = True
            continue
        if not collecting:
            continue
        item = ITEM.match(line)
        if item is None:
            break
        sources.add(item.group(1).strip().strip("'\""))
    return sources
