"""Check the selected wiki's index and links without writing derived files."""

from tools.graph.scan_pages import scan_pages
from tools.index.index_stale import index_stale
from tools.index.ordered_page_directories import ordered_page_directories
from tools.index.page_convention_issues import page_convention_issues
from tools.index.syntopica_config import SyntopicaConfig


def brain_lint(config: SyntopicaConfig) -> int:
    """Report stale index, dangling links and schema breaches as failures."""
    directories = ordered_page_directories(config.pages)
    pages = scan_pages(config.index.parent, directories)
    issues = sorted(
        [
            f"dangling: {page['id']} -> [[{target}]]"
            for page in pages.values()
            for target in set(page["targets"])
            if target not in pages
        ]
        + [message for _, _, message in page_convention_issues(config.index.parent, directories)]
    )
    if index_stale(config, directories):
        issues.append("index is out of date; run brain index")
    for issue in issues:
        print(issue)
    print(f"lint: {len(pages)} pages, {len(issues)} issues")
    return int(bool(issues))
