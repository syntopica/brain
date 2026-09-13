"""Print related: extracted from build.py."""

from tools.graph.page import Page
from tools.graph.related_pairs import related_pairs

TOP_RELATED = 10


def print_related(pages: dict[str, Page], neighbours: dict[str, set[str]]) -> None:
    """Print the best-scoring unlinked pairs, and count the tail behind them."""
    pairs = related_pairs(pages, neighbours)
    for score, left, right in pairs[:TOP_RELATED]:
        print(f"  related but unlinked ({score:.1f}): {left} <-> {right}")
    if len(pairs) > TOP_RELATED:
        # The tail is long and shallow by construction - anything above type
        # affinity qualifies - so it is counted with its floor named rather
        # than printed or silently cut.
        print(
            f"  ... and {len(pairs) - TOP_RELATED} more scoring above 1.0, "
            f"down to {pairs[-1][0]:.1f}"
        )
