"""The page pairs that look related and that nothing links."""

# These modules are scripts run from their own directory, so at runtime they
# import each other by bare name. mypy names every file by its path from the
# repository root instead, and cannot be told otherwise: two tools are called
# build.py, so tools/graph cannot join mypy_path without a module collision.
# Hence the pair - the checked branch and the executed one, same names.
from tools.graph.page import Page
from tools.graph.pair_score import TYPE_AFFINITY, pair_score


def related_pairs(
    pages: dict[str, Page], neighbours: dict[str, set[str]]
) -> list[tuple[float, str, str]]:
    """Unlinked pairs scoring above type affinity alone, highest first.

    Linked pairs are dropped rather than scored and shown, because the reason to
    score at all is SCHEMA's connect-or-shelve rule: what is worth reading is
    the pair the wiki should already have connected and has not. Sharing only a
    `type` is dropped for the same reason - every pair of topic pages shares
    that, so it is not on its own a reason to link anything.
    """
    scored: list[tuple[float, str, str]] = []
    ids = sorted(pages)
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            if right in neighbours[left]:
                continue
            score = pair_score(pages[left], pages[right], neighbours)
            if score > TYPE_AFFINITY:
                scored.append((score, left, right))
    scored.sort(key=lambda pair: (-pair[0], pair[1], pair[2]))
    return scored
