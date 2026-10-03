"""The links that name a page the scan did not find."""

from tools.graph.page import Page


def dangling_links(pages: dict[str, Page]) -> list[tuple[str, str]]:
    """Every distinct `(source, target)` whose target is not a page, sorted."""
    return sorted(
        {
            (page["id"], target)
            for page in pages.values()
            for target in page["targets"]
            if target not in pages
        }
    )
