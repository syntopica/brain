"""Parse frontmatter: extracted from build.py."""

import re

FENCE = len("---")


def parse_frontmatter(text: str) -> dict[str, str]:
    """The `title`, `type` and `updated` keys of a page's frontmatter.

    Only those three, because they are the only scalars the viewer shows;
    `sources` is a block list and is read by `frontmatter_sources`. A page with
    no frontmatter, or one whose block is never closed, yields an empty mapping
    rather than an error - a single malformed page must not stop the graph
    being drawn.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", FENCE)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^(title|type|updated):\s*(.+)$", line.strip())
        if m:
            fields[m.group(1)] = m.group(2).strip().strip("'\"")
    return fields
