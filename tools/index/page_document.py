"""One page's frontmatter, body and links as a document."""

from pathlib import Path
from typing import Any

from tools.graph.frontmatter_sources import frontmatter_sources
from tools.graph.page import Page
from tools.graph.parse_frontmatter import parse_frontmatter
from tools.index.raw_summary import raw_summary

SCHEMA_VERSION = 1
BODY_CAP = 1024 * 1024
# Room for the frontmatter in front of a capped body, so a page at the cap is
# read once and never whole when it is far larger.
HEAD_ALLOWANCE = 64 * 1024
FENCE = len("---")


def page_document(page_id: str, path: Path, pages: dict[str, Page]) -> dict[str, Any]:
    """The page as stored, its body capped at 1 MiB, and its resolved links."""
    size = path.stat().st_size
    with path.open("rb") as handle:
        head = handle.read(BODY_CAP + HEAD_ALLOWANCE)
    text = head.decode("utf-8", errors="replace")
    end = text.find("\n---", FENCE) if text.startswith("---") else -1
    block = text[FENCE:end] if end != -1 else ""
    newline = text.find("\n", end + 1 + FENCE) if end != -1 else -1
    body = text if end == -1 else "" if newline == -1 else text[newline + 1 :]
    encoded = body.encode("utf-8")
    truncated = size > len(head) or len(encoded) > BODY_CAP
    if len(encoded) > BODY_CAP:
        body = encoded[:BODY_CAP].decode("utf-8", errors="ignore")
    frontmatter: dict[str, Any] = dict(parse_frontmatter(text))
    if summary := raw_summary(block).strip("'\""):
        frontmatter["summary"] = summary
    frontmatter["sources"] = sorted(frontmatter_sources(text))
    targets = dict.fromkeys(pages[page_id]["targets"]) if page_id in pages else {}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "id": page_id,
        "frontmatter": frontmatter,
        "body": body,
        "truncated": truncated,
        "links": {
            "outbound": [{"target": target, "exists": target in pages} for target in targets],
            "inbound": sorted(
                other
                for other, page in pages.items()
                if other != page_id and page_id in page["targets"]
            ),
        },
    }
