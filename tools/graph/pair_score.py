"""How related two pages are, on nashsu's weights."""

from math import log

# These modules are scripts run from their own directory, so at runtime they
# import each other by bare name. mypy names every file by its path from the
# repository root instead, and cannot be told otherwise: two tools are called
# build.py, so tools/graph cannot join mypy_path without a module collision.
# Hence the pair - the checked branch and the executed one, same names.
from tools.graph.page import Page

SOURCE_OVERLAP = 4.0
ADAMIC_ADAR = 1.5
TYPE_AFFINITY = 1.0


def pair_score(left: Page, right: Page, neighbours: dict[str, set[str]]) -> float:
    """The weights come from nashsu, read in the 2026-08-02 ecosystem survey.

    Shared sources dominate, because two pages written from the same article
    are about the same thing whatever they are called. Adamic-Adar rewards a
    shared neighbour that is not a hub - 1/log(degree), so a page linked from
    everywhere counts for little and a page linked from three counts for a lot.
    Same type is the weakest signal and is deliberately worth less than either
    of the others alone.

    nashsu's fourth weight, a direct link at 3.0, is absent: the only pairs
    worth scoring here are the ones with no link, so the term would be zero
    everywhere it is evaluated.
    """
    shared_sources = left["sources"] & right["sources"]
    smaller = min(len(left["sources"]), len(right["sources"]))
    overlap = len(shared_sources) / smaller if smaller else 0.0
    shared_neighbours = neighbours[left["id"]] & neighbours[right["id"]]
    adamic = sum(
        1 / log(len(neighbours[common]))
        for common in shared_neighbours
        if len(neighbours[common]) > 1
    )
    same_type = 1.0 if left["type"] == right["type"] else 0.0
    return SOURCE_OVERLAP * overlap + ADAMIC_ADAR * adamic + TYPE_AFFINITY * same_type
