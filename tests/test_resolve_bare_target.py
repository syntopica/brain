"""A link without its directory resolves when exactly one page answers to it."""

from pathlib import Path

from tests.fixtures.make_data_directory import make_data_directory
from tools.graph.resolve_bare_target import resolve_bare_target
from tools.graph.scan_pages import scan_pages
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.ordered_page_directories import ordered_page_directories

PAGE = "---\ntitle: T\ntype: note\nupdated: 2026-01-01\nsummary: S\n---\n"


def test_one_match_resolves() -> None:
    assert resolve_bare_target("decisions", {"decisions": ("pages/decisions",)}) == (
        "pages/decisions"
    )


def test_several_matches_stay_unresolved_for_the_caller_to_report() -> None:
    assert resolve_bare_target("x", {"x": ("a/x", "b/x")}) == "x"


def test_a_citation_marker_that_names_no_page_is_not_a_link() -> None:
    assert resolve_bare_target("S1", {"decisions": ("pages/decisions",)}) is None


def test_the_scanner_links_a_bare_target_to_the_page_it_names(tmp_path: Path) -> None:
    root = make_data_directory(
        tmp_path,
        {
            "notes/start.md": f"{PAGE}\nSee [[decisions]], and cite [[S1]].\n",
            "notes/decisions.md": PAGE,
        },
    )
    config = load_syntopica_config(root, {})
    pages = scan_pages(config.index.parent, ordered_page_directories(config.pages))
    assert pages["notes/start"]["targets"] == ["notes/decisions"]
