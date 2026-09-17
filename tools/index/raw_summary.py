"""Raw summary: the `summary:` scalar as frontmatter stores it."""

from tools.index.folded_value import folded_value


def raw_summary(block: str) -> str:
    """The `summary:` value, joined back up if it spans several lines."""
    return folded_value(block, "summary")
