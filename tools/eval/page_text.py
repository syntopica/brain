"""Everything on a page a search may match, lowercased."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.eval.page import Page


def page_text(page: "Page") -> str:
    """Return title, summary and body of `page` as one lowercased string.

    Only ever asked whether a term is present, never where - the weighting of
    where lives in `keyword_scores`, which reads the three fields separately.
    """
    return f"{page['title']} {page['summary']} {page['body']}".lower()
