"""Every wiki page as the two things retrieval scores: its text and its links."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.eval.page import Page

PAGE_DIRS = ["projects", "business", "people", "topics", "personal"]
LINK = re.compile(r"\[\[([^\]|#]+)")
SUMMARY = re.compile(r"^summary:\s*(.+)$", re.M)
TITLE = re.compile(r"^title:\s*(.+)$", re.M)


def load_pages(root: Path) -> dict[str, "Page"]:
    """Read every scored page under `root`, keyed by page id.

    Keyed by page id (`topics/llm-wiki`), the same id `queries.toml` names
    and `tools/graph/build.py` uses, so a ground-truth entry and a graph finding
    are talking about the same thing.

    `index.md` is deliberately absent, for the graph's reason one step further
    on: it lists every page by construction, so a retrieval baseline that could
    return it would score a hit on every question ever asked. The reader starts
    there; the measurement is about where they go next.

    Title and summary are kept apart from the body because they are what a
    reader sees first under SCHEMA's query discipline - frontmatter and the
    summary paragraph before anything else - and a baseline that ignored that
    ordering would not be scoring the discipline the wiki actually states.
    """
    pages: dict[str, Page] = {}
    for directory in PAGE_DIRS:
        for path in sorted((root / directory).glob("*.md")):
            page_id = f"{directory}/{path.stem}"
            text = path.read_text(encoding="utf-8")
            end = text.find("\n---", 3)
            front = text[3:end] if text.startswith("---") and end != -1 else ""
            body = text[end + 4 :] if end != -1 else text
            title = TITLE.search(front)
            summary = SUMMARY.search(front)
            pages[page_id] = {
                "id": page_id,
                "title": title.group(1).strip().strip("'\"") if title else path.stem,
                "summary": summary.group(1).strip().strip("'\"") if summary else "",
                "body": body,
                "links": {
                    target.strip()
                    for target in LINK.findall(re.sub(r"`[^`]*`", "", body))
                    if "/" in target
                },
            }
    for page in pages.values():
        page["links"] = {target for target in page["links"] if target in pages}
    return pages
