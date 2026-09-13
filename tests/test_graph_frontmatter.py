"""Frontmatter source extraction used by graph scanning."""

from tools.graph.frontmatter_sources import frontmatter_sources


def test_sources_are_read_from_the_block_list() -> None:
    text = "---\ntitle: A\nsources:\n  - https://one\n  - https://two\n---\nbody\n"
    assert frontmatter_sources(text) == {"https://one", "https://two"}


def test_source_entries_are_unquoted() -> None:
    text = "---\nsources:\n  - 'https://one'\n  - \"https://two\"\n---\n"
    assert frontmatter_sources(text) == {"https://one", "https://two"}


def test_the_block_stops_at_the_next_key() -> None:
    """A later key ends the list; its value must not be read as a source."""
    text = "---\nsources:\n  - https://one\nupdated: 2026-01-01\n  - https://two\n---\n"
    assert frontmatter_sources(text) == {"https://one"}


def test_a_page_with_no_frontmatter_has_no_sources() -> None:
    assert frontmatter_sources("# just a body\n") == set()


def test_an_unterminated_frontmatter_yields_no_sources_rather_than_raising() -> None:
    """One malformed page must not stop the graph being drawn."""
    assert frontmatter_sources("---\nsources:\n  - https://one\n") == set()
