"""The links between two different existing pages, each counted once."""

from tools.graph.page import Page


def distinct_edges(pages: dict[str, Page]) -> list[list[str]]:
    """Every `[source, target]` link to another page that exists, in body order.

    A repeated link is one edge and a self-link is no edge: the first would
    double a degree, the second is a defect the text report names separately.
    """
    edges: list[list[str]] = []
    for page in pages.values():
        for target in dict.fromkeys(page["targets"]):
            if target in pages and target != page["id"]:
                edges.append([page["id"], target])
    return edges
