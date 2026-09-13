"""Personalized PageRank over the wikilink graph, seeded by a question."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.eval.page import Page

DAMPING = 0.85
ITERATIONS = 30


def pagerank_scores(seed: dict[str, float], pages: dict[str, "Page"]) -> dict[str, float]:
    """Rank every page by a walk from `seed` over the wikilink graph.

    `green-dalii`'s comparison, and the only baseline here that scores the
    graph rather than the prose: the walk starts wherever the question's words
    landed and follows `[[links]]` the way SCHEMA tells a reader to.

    Links are followed both ways. A page's inbound links are how a reader
    arrives at it from a hub, and the graph build already reports 14 pages that
    link to no other page - treating the edges as directed would score those
    as unreachable when a reader reaches them every day from the page that
    names them.

    An all-zero seed - a question whose words appear nowhere - returns an
    all-zero ranking rather than the graph's own centrality. That is the honest
    answer: it says the wiki has nothing, which is what `expected_refusal` is
    for, and a centrality ranking would dress up "no idea" as five confident
    pages.
    """
    total_seed = sum(seed.values())
    if total_seed <= 0:
        return dict.fromkeys(pages, 0.0)
    restart = {page_id: weight / total_seed for page_id, weight in seed.items()}
    neighbours = {
        page_id: page["links"]
        | {other for other, candidate in pages.items() if page_id in candidate["links"]}
        for page_id, page in pages.items()
    }
    rank = dict(restart)
    for _ in range(ITERATIONS):
        spread = dict.fromkeys(pages, 0.0)
        for page_id, weight in rank.items():
            targets = neighbours[page_id]
            if not targets:
                spread[page_id] += weight
                continue
            share = weight / len(targets)
            for target in targets:
                spread[target] += share
        rank = {
            page_id: (1 - DAMPING) * restart.get(page_id, 0.0) + DAMPING * spread[page_id]
            for page_id in pages
        }
    return rank
