"""Parse frontmatter: extracted from build.py."""

from tools.index.folded_value import folded_value

FENCE = len("---")
FIELDS = ("title", "type", "updated")


def parse_frontmatter(text: str) -> dict[str, str]:
    """The `title`, `type` and `updated` keys of a page's frontmatter.

    Only those three, because they are the only scalars the viewer shows;
    `sources` is a block list and is read by `frontmatter_sources`. A page with
    no frontmatter, or one whose frontmatter is never closed, yields an empty
    mapping rather than an error - a single malformed page must not stop the
    graph being drawn.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", FENCE)
    if end == -1:
        return {}
    block = text[3:end]
    fields = {}
    for field in FIELDS:
        value = folded_value(block, field).strip().strip("'\"")
        if value:
            fields[field] = value
    return fields
