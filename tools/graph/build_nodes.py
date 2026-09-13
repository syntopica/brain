"""Build nodes: extracted from build.py."""

from tools.graph.node import Node
from tools.graph.page import Page


def build_nodes(pages: dict[str, Page], inbound: dict[str, list[str]]) -> list[Node]:
    """One node per page, with the two degrees the viewer sizes by.

    Outbound counts distinct pages that exist, never link occurrences, and
    never the page itself: a self-link is reported as a defect, not drawn.
    """
    nodes: list[Node] = []
    for p in pages.values():
        outbound = sum(1 for t in dict.fromkeys(p["targets"]) if t in pages and t != p["id"])
        nodes.append(
            {
                "id": p["id"],
                "title": p["title"],
                "type": p["type"],
                "dir": p["dir"],
                "updated": p["updated"],
                "in": len(inbound[p["id"]]),
                "out": outbound,
            }
        )
    return nodes
