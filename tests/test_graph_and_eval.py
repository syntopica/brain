"""The two scoring rules the wiki's own tooling depends on.

`pair_score` decides which unlinked pages get suggested as related, and
`query_terms` decides what a question is actually searching for. Both are
pure, both encode a judgment call that is easy to break silently, and neither
had a test.
"""

import importlib.util
import sys
from math import log
from pathlib import Path

import pytest

from tests.tool_paths import TOOLS_ROOT


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


@pytest.fixture(scope="module")
def pair_score():
    return _load("pair_score", TOOLS_ROOT / "graph" / "pair_score.py")


@pytest.fixture(scope="module")
def query_terms():
    return _load("query_terms", TOOLS_ROOT / "eval" / "query_terms.py")


def _page(page_id: str, sources: set[str], page_type: str = "topic") -> dict:
    return {"id": page_id, "sources": sources, "type": page_type}


def test_two_pages_sharing_nothing_score_only_their_type(pair_score) -> None:
    left, right = _page("a", {"s1"}), _page("b", {"s2"})
    neighbours = {"a": set(), "b": set()}
    assert pair_score.pair_score(left, right, neighbours) == pytest.approx(pair_score.TYPE_AFFINITY)


def test_a_different_type_removes_the_weakest_signal(pair_score) -> None:
    left, right = _page("a", {"s1"}), _page("b", {"s2"}, page_type="project")
    neighbours = {"a": set(), "b": set()}
    assert pair_score.pair_score(left, right, neighbours) == pytest.approx(0.0)


def test_shared_sources_dominate_the_score(pair_score) -> None:
    left, right = _page("a", {"s1", "s2"}), _page("b", {"s1", "s2"})
    neighbours = {"a": set(), "b": set()}
    score = pair_score.pair_score(left, right, neighbours)
    assert score == pytest.approx(pair_score.SOURCE_OVERLAP + pair_score.TYPE_AFFINITY)


def test_overlap_is_measured_against_the_smaller_page(pair_score) -> None:
    """One shared source out of one is total overlap, however large the other."""
    left, right = _page("a", {"s1"}), _page("b", {"s1", "s2", "s3", "s4"})
    neighbours = {"a": set(), "b": set()}
    score = pair_score.pair_score(left, right, neighbours)
    assert score == pytest.approx(pair_score.SOURCE_OVERLAP + pair_score.TYPE_AFFINITY)


def test_a_page_with_no_sources_does_not_divide_by_zero(pair_score) -> None:
    left, right = _page("a", set()), _page("b", {"s1"})
    neighbours = {"a": set(), "b": set()}
    assert pair_score.pair_score(left, right, neighbours) == pytest.approx(pair_score.TYPE_AFFINITY)


def test_a_hub_neighbour_counts_for_less_than_a_rare_one(pair_score) -> None:
    """That is the whole point of Adamic-Adar, so it is worth asserting."""
    neighbours_rare = {"a": {"n"}, "b": {"n"}, "n": {"a", "b"}}
    neighbours_hub = {"a": {"n"}, "b": {"n"}, "n": set("abcdefghij")}
    rare = pair_score.pair_score(_page("a", set()), _page("b", set()), neighbours_rare)
    hub = pair_score.pair_score(_page("a", set()), _page("b", set()), neighbours_hub)
    assert rare > hub


def test_a_neighbour_linked_only_once_contributes_nothing(pair_score) -> None:
    """1/log(1) is a division by zero; the rule skips those instead."""
    neighbours = {"a": {"n"}, "b": {"n"}, "n": {"a"}}
    score = pair_score.pair_score(_page("a", set()), _page("b", set()), neighbours)
    assert score == pytest.approx(pair_score.TYPE_AFFINITY)


def test_the_adamic_adar_term_is_the_documented_formula(pair_score) -> None:
    neighbours = {"a": {"n"}, "b": {"n"}, "n": {"a", "b", "c"}}
    score = pair_score.pair_score(_page("a", set()), _page("b", set()), neighbours)
    expected = pair_score.ADAMIC_ADAR * (1 / log(3)) + pair_score.TYPE_AFFINITY
    assert score == pytest.approx(expected)


def test_function_words_are_dropped(query_terms) -> None:
    assert query_terms.query_terms("what is the modelo 303") == ["modelo", "303"]


def test_a_dotted_name_survives_as_one_term(query_terms) -> None:
    assert "example.org" in query_terms.query_terms("how is example.org deployed")


def test_a_hyphenated_name_survives_as_one_term(query_terms) -> None:
    assert "sample-archive" in query_terms.query_terms("where do sample-archive live")


def test_single_characters_are_not_terms(query_terms) -> None:
    assert query_terms.query_terms("a b c modelo") == ["modelo"]


def test_repeats_are_kept_because_they_weigh_the_question(query_terms) -> None:
    assert query_terms.query_terms("holded holded invoice") == [
        "holded",
        "holded",
        "invoice",
    ]
