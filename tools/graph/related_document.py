"""The best-scoring related-but-unlinked page pairs as a document."""

from typing import Any

from tools.graph.distinct_edges import distinct_edges
from tools.graph.page import Page
from tools.graph.related_pairs import related_pairs
from tools.graph.undirected_neighbours import undirected_neighbours

SCHEMA_VERSION = 1


def related_document(pages: dict[str, Page], limit: int) -> dict[str, Any]:
    """The top `limit` pairs, highest score first, and how many qualified."""
    pairs = related_pairs(pages, undirected_neighbours(pages, distinct_edges(pages)))
    return {
        "schemaVersion": SCHEMA_VERSION,
        "total": len(pairs),
        "pairs": [
            {"left": left, "right": right, "score": round(score, 3)}
            for score, left, right in pairs[:limit]
        ],
    }
