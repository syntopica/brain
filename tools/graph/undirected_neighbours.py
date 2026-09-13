"""Undirected neighbours: extracted from build.py."""

from tools.graph.page import Page


def undirected_neighbours(pages: dict[str, Page], edges: list[list[str]]) -> dict[str, set[str]]:
    """Every page's neighbours, ignoring which end of a link wrote it.

    Undirected on purpose: relatedness and reachability do not care about
    direction, and the viewer shows inbound and outbound alike.
    """
    neighbours: dict[str, set[str]] = {pid: set() for pid in pages}
    for source, target in edges:
        neighbours[source].add(target)
        neighbours[target].add(source)
    return neighbours
