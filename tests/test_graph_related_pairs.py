"""Related-pair ranking without implicit module-root configuration."""

from tools.graph.related_pairs import related_pairs


def _scored(page_id: str, sources: set[str], page_type: str = "topic") -> dict[str, object]:
    return {"id": page_id, "sources": sources, "type": page_type}


def test_an_already_linked_pair_is_never_suggested() -> None:
    pages = {"a": _scored("a", {"s"}), "b": _scored("b", {"s"})}
    assert related_pairs(pages, {"a": {"b"}, "b": {"a"}}) == []


def test_sharing_only_a_type_is_not_a_reason_to_link() -> None:
    """Every pair of topic pages shares a type, so the floor is exclusive."""
    pages = {"a": _scored("a", {"s1"}), "b": _scored("b", {"s2"})}
    assert related_pairs(pages, {"a": set(), "b": set()}) == []


def test_a_shared_source_makes_an_unlinked_pair() -> None:
    pages = {"a": _scored("a", {"s"}), "b": _scored("b", {"s"})}
    pairs = related_pairs(pages, {"a": set(), "b": set()})
    assert [(left, right) for _, left, right in pairs] == [("a", "b")]


def test_pairs_come_back_highest_first_then_alphabetically() -> None:
    pages = {
        "a": _scored("a", {"s"}),
        "b": _scored("b", {"s"}),
        "c": _scored("c", {"s"}),
        "z": _scored("z", set(), page_type="project"),
    }
    neighbours: dict[str, set[str]] = {"a": set(), "b": set(), "c": set(), "z": set()}
    pairs = related_pairs(pages, neighbours)
    assert [(left, right) for _, left, right in pairs] == [("a", "b"), ("a", "c"), ("b", "c")]
    assert [round(score, 6) for score, _, _ in pairs] == [5.0, 5.0, 5.0]


def test_each_pair_is_reported_once() -> None:
    pages = {"a": _scored("a", {"s"}), "b": _scored("b", {"s"})}
    pairs = related_pairs(pages, {"a": set(), "b": set()})
    assert len(pairs) == 1
