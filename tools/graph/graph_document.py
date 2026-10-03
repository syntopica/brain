"""The link graph as a machine-readable document, without writing anything."""

from typing import Any

from tools.graph.dangling_links import dangling_links
from tools.graph.distinct_edges import distinct_edges
from tools.graph.page import Page

SCHEMA_VERSION = 1


def graph_document(pages: dict[str, Page]) -> dict[str, Any]:
    """Nodes, edges, orphans and dangling links; titles and bodies left out.

    Related-unlinked pairs are absent on purpose: scoring them is quadratic in
    the page count, and this document is polled. They have their own on-demand
    document. A title is page content, so a node carries only its id, type and
    degree (distinct pages linked in either direction, as the viewer counts).
    """
    edges = distinct_edges(pages)
    inbound = dict.fromkeys(pages, 0)
    outbound = dict.fromkeys(pages, 0)
    for source, target in edges:
        outbound[source] += 1
        inbound[target] += 1
    return {
        "schemaVersion": SCHEMA_VERSION,
        "nodes": [
            {"id": page_id, "type": page["type"], "degree": inbound[page_id] + outbound[page_id]}
            for page_id, page in pages.items()
        ],
        "edges": [{"source": source, "target": target} for source, target in edges],
        "orphans": sorted(page_id for page_id, count in inbound.items() if count == 0),
        "dangling": [
            {"page": source, "target": target} for source, target in dangling_links(pages)
        ],
    }
