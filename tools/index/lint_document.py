"""The lint findings as a machine-readable document, without page content."""

from typing import Any

from tools.graph.dangling_links import dangling_links
from tools.graph.scan_pages import scan_pages
from tools.index.index_stale import index_stale
from tools.index.ordered_page_directories import ordered_page_directories
from tools.index.page_convention_issues import page_convention_issues
from tools.index.syntopica_config import SyntopicaConfig

SCHEMA_VERSION = 1


def lint_document(config: SyntopicaConfig) -> dict[str, Any]:
    """Distinct `(page, code)` issues, sorted, and whether the index is stale.

    Codes, not messages: a message can quote a link target the author wrote,
    and a reader that stores or displays findings must not carry content.
    """
    directories = ordered_page_directories(config.pages)
    pages = scan_pages(config.index.parent, directories)
    issues = {(source, "dangling_link") for source, _ in dangling_links(pages)} | {
        (page, code) for page, code, _ in page_convention_issues(config.index.parent, directories)
    }
    return {
        "schemaVersion": SCHEMA_VERSION,
        "pageCount": len(pages),
        "indexStale": index_stale(config, directories),
        "issues": [{"page": page, "code": code} for page, code in sorted(issues)],
    }
