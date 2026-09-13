"""The retrieval baselines in tools/eval, scored on what they actually decide.

`tools/eval/run.py` prints two numbers that a reader takes as a fact about the
wiki's cross-linking. Every judgment behind those numbers - which text counts
as a page, which `[[link]]` is real, how a term's rarity is weighted, when a
baseline is allowed to return nothing - lives in these five pure functions and
none of them had a test. Nothing here touches the real wiki: pages are built
in memory or in a tmp dir.
"""

import importlib.util
import sys
from math import log
from pathlib import Path

import pytest

from tests.tool_paths import TOOLS_ROOT

EVAL_ROOT = TOOLS_ROOT / "eval"


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
def load_pages():
    return _load("load_pages", EVAL_ROOT / "load_pages.py")


@pytest.fixture(scope="module")
def page_text():
    return _load("page_text", EVAL_ROOT / "page_text.py")


@pytest.fixture(scope="module")
def keyword_scores():
    return _load("keyword_scores", EVAL_ROOT / "keyword_scores.py")


@pytest.fixture(scope="module")
def pagerank_scores():
    return _load("pagerank_scores", EVAL_ROOT / "pagerank_scores.py")


@pytest.fixture(scope="module")
def recall_at_k():
    return _load("recall_at_k", EVAL_ROOT / "recall_at_k.py")


@pytest.fixture(scope="module")
def top_pages():
    return _load("top_pages", EVAL_ROOT / "top_pages.py")


def _page(page_id, title="", summary="", body="", links=()):
    return {
        "id": page_id,
        "title": title,
        "summary": summary,
        "body": body,
        "links": set(links),
    }


def _wiki(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


# --- load_pages: what counts as a page, and what it is made of ---------------


def test_a_page_id_is_directory_plus_stem(load_pages, tmp_path) -> None:
    root = _wiki(tmp_path, {"topics/llm-wiki.md": "---\ntitle: LLM Wiki\n---\nbody"})
    assert set(load_pages.load_pages(root)) == {"topics/llm-wiki"}


def test_frontmatter_title_and_summary_are_split_off_the_body(load_pages, tmp_path) -> None:
    root = _wiki(
        tmp_path,
        {"topics/a.md": "---\ntitle: 'The Title'\nsummary: \"The summary\"\n---\nThe body\n"},
    )
    page = load_pages.load_pages(root)["topics/a"]
    assert page["title"] == "The Title"
    assert page["summary"] == "The summary"
    assert "title:" not in page["body"]
    assert "The body" in page["body"]


def test_a_page_without_frontmatter_falls_back_to_its_filename(load_pages, tmp_path) -> None:
    root = _wiki(tmp_path, {"topics/tgss-headless.md": "just prose\n"})
    page = load_pages.load_pages(root)["topics/tgss-headless"]
    assert page["title"] == "tgss-headless"
    assert page["summary"] == ""
    assert page["body"] == "just prose\n"


def test_only_the_five_page_directories_are_loaded(load_pages, tmp_path) -> None:
    root = _wiki(
        tmp_path,
        {
            "topics/a.md": "a",
            "sources/vault/b.md": "b",
            "docs/c.md": "c",
        },
    )
    assert set(load_pages.load_pages(root)) == {"topics/a"}


def test_index_is_not_a_page_because_it_links_to_everything(load_pages, tmp_path) -> None:
    root = _wiki(tmp_path, {"topics/a.md": "a", "index.md": "[[topics/a]]"})
    assert "index" not in load_pages.load_pages(root)


def test_a_wikilink_keeps_the_target_and_drops_alias_and_anchor(load_pages, tmp_path) -> None:
    root = _wiki(
        tmp_path,
        {
            "topics/a.md": "see [[topics/b|the other one]] and [[topics/c#section]]\n",
            "topics/b.md": "b",
            "topics/c.md": "c",
        },
    )
    assert load_pages.load_pages(root)["topics/a"]["links"] == {"topics/b", "topics/c"}


def test_a_link_inside_a_code_span_is_not_a_link(load_pages, tmp_path) -> None:
    root = _wiki(
        tmp_path,
        {"topics/a.md": "write `[[topics/b]]` to link\n", "topics/b.md": "b"},
    )
    assert load_pages.load_pages(root)["topics/a"]["links"] == set()


def test_a_bare_word_link_without_a_directory_is_not_a_page_link(load_pages, tmp_path) -> None:
    root = _wiki(tmp_path, {"topics/a.md": "[[glossary]]\n"})
    assert load_pages.load_pages(root)["topics/a"]["links"] == set()


def test_a_link_to_a_page_that_does_not_exist_is_pruned(load_pages, tmp_path) -> None:
    root = _wiki(tmp_path, {"topics/a.md": "[[topics/b]] [[topics/gone]]\n", "topics/b.md": "b"})
    assert load_pages.load_pages(root)["topics/a"]["links"] == {"topics/b"}


def test_a_page_with_no_wiki_directories_at_all_loads_nothing(load_pages, tmp_path) -> None:
    assert load_pages.load_pages(tmp_path) == {}


def test_a_horizontal_rule_in_a_page_without_frontmatter_eats_the_head(
    load_pages, tmp_path
) -> None:
    """Documents today's behaviour, which is a bug - see the pass report.

    The frontmatter terminator is searched for whether or not the page opens
    with one, so a `---` rule in a page that has no frontmatter truncates the
    body at that rule instead of leaving it whole.
    """
    root = _wiki(tmp_path, {"topics/a.md": "opening line\n---\nrest of the page\n"})
    body = load_pages.load_pages(root)["topics/a"]["body"]
    assert "opening line" not in body
    assert body == "\nrest of the page\n"


# --- page_text ---------------------------------------------------------------


def test_page_text_joins_the_three_fields_lowercased(page_text) -> None:
    page = _page("topics/a", title="Title", summary="Summary", body="BODY")
    assert page_text.page_text(page) == "title summary body"


# --- keyword_scores: the weighting the eval exists to measure -----------------


def test_a_title_hit_outweighs_a_summary_hit_which_outweighs_the_body(keyword_scores) -> None:
    pages = {
        "t": _page("t", title="holded"),
        "s": _page("s", summary="holded"),
        "b": _page("b", body="holded"),
    }
    scores = keyword_scores.keyword_scores("holded", pages)
    assert scores["t"] > scores["s"] > scores["b"] > 0


def test_body_mentions_saturate_so_length_cannot_win_a_question(keyword_scores) -> None:
    pages = {
        "few": _page("few", body="holded " * 3),
        "many": _page("many", body="holded " * 40),
    }
    scores = keyword_scores.keyword_scores("holded", pages)
    assert scores["few"] == pytest.approx(scores["many"])


def test_a_term_every_page_carries_is_worth_less_than_a_rare_one(keyword_scores) -> None:
    pages = {
        "a": _page("a", title="common rare"),
        "b": _page("b", title="common"),
        "c": _page("c", title="common"),
    }
    scores = keyword_scores.keyword_scores("common", pages)
    rare = keyword_scores.keyword_scores("rare", pages)
    assert rare["a"] > scores["a"]


def test_a_term_no_page_carries_contributes_nothing_rather_than_raising(keyword_scores) -> None:
    pages = {"a": _page("a", title="holded")}
    assert keyword_scores.keyword_scores("cloudflare", pages) == {"a": 0.0}


def test_a_question_of_only_stop_words_scores_every_page_zero(keyword_scores) -> None:
    pages = {"a": _page("a", title="holded"), "b": _page("b", title="cloudflare")}
    assert keyword_scores.keyword_scores("what is the", pages) == {"a": 0.0, "b": 0.0}


def test_the_weighting_is_the_documented_formula(keyword_scores) -> None:
    """One page, one term: rarity is log(1/1)+1, and all three fields hit once."""
    pages = {"a": _page("a", title="holded", summary="holded", body="holded")}
    expected = (log(1.0) + 1.0) * (
        keyword_scores.TITLE_WEIGHT + keyword_scores.SUMMARY_WEIGHT + keyword_scores.BODY_WEIGHT
    )
    assert keyword_scores.keyword_scores("holded", pages)["a"] == pytest.approx(expected)


def test_a_repeated_query_term_counts_twice(keyword_scores) -> None:
    pages = {"a": _page("a", title="holded")}
    once = keyword_scores.keyword_scores("holded", pages)["a"]
    twice = keyword_scores.keyword_scores("holded holded", pages)["a"]
    assert twice == pytest.approx(2 * once)


# --- pagerank_scores ---------------------------------------------------------


def test_an_all_zero_seed_returns_an_all_zero_ranking(pagerank_scores) -> None:
    pages = {"a": _page("a", links={"b"}), "b": _page("b")}
    assert pagerank_scores.pagerank_scores({"a": 0.0}, pages) == {"a": 0.0, "b": 0.0}


def test_an_empty_seed_returns_an_all_zero_ranking(pagerank_scores) -> None:
    pages = {"a": _page("a"), "b": _page("b")}
    assert pagerank_scores.pagerank_scores({}, pages) == {"a": 0.0, "b": 0.0}


def test_rank_flows_to_a_neighbour_of_the_seed(pagerank_scores) -> None:
    pages = {"a": _page("a", links={"b"}), "b": _page("b"), "c": _page("c")}
    rank = pagerank_scores.pagerank_scores({"a": 1.0}, pages)
    assert rank["b"] > rank["c"]


def test_an_inbound_link_is_followed_as_well_as_an_outbound_one(pagerank_scores) -> None:
    """The 14 pages that link to nothing are reached from the hubs that name them."""
    pages = {"hub": _page("hub", links={"leaf"}), "leaf": _page("leaf"), "far": _page("far")}
    rank = pagerank_scores.pagerank_scores({"leaf": 1.0}, pages)
    assert rank["hub"] > rank["far"]


def test_an_isolated_seed_keeps_its_own_rank(pagerank_scores) -> None:
    pages = {"a": _page("a"), "b": _page("b")}
    rank = pagerank_scores.pagerank_scores({"a": 1.0}, pages)
    assert rank["a"] > rank["b"]
    assert rank["b"] == pytest.approx(0.0)


def test_a_seed_is_normalised_so_only_its_shape_matters(pagerank_scores) -> None:
    pages = {"a": _page("a", links={"b"}), "b": _page("b"), "c": _page("c")}
    small = pagerank_scores.pagerank_scores({"a": 1.0, "c": 1.0}, pages)
    large = pagerank_scores.pagerank_scores({"a": 500.0, "c": 500.0}, pages)
    for page_id in pages:
        assert small[page_id] == pytest.approx(large[page_id])


def test_a_seed_page_missing_from_the_graph_raises_today(pagerank_scores) -> None:
    """Documents today's behaviour, which is a latent bug - see the pass report.

    `run.py` only ever seeds from `keyword_scores` over the same page set, so
    this cannot happen there; a second caller seeding from anywhere else gets a
    `KeyError` rather than a ranking that ignores the unknown id.
    """
    pages = {"a": _page("a")}
    with pytest.raises(KeyError):
        pagerank_scores.pagerank_scores({"ghost": 1.0}, pages)


# --- recall_at_k -------------------------------------------------------------


def test_recall_is_the_share_of_expected_pages_found(recall_at_k) -> None:
    assert recall_at_k.recall_at_k(["a", "x", "y"], ["a", "b"]) == pytest.approx(0.5)


def test_extra_retrieved_pages_do_not_cost_anything(recall_at_k) -> None:
    assert recall_at_k.recall_at_k(["a", "b", "x", "y", "z"], ["a", "b"]) == 1.0


def test_a_refusal_question_scores_one_only_when_nothing_was_returned(recall_at_k) -> None:
    assert recall_at_k.recall_at_k([], []) == 1.0
    assert recall_at_k.recall_at_k(["a"], []) == 0.0


def test_finding_none_of_the_expected_pages_scores_zero(recall_at_k) -> None:
    assert recall_at_k.recall_at_k(["x"], ["a", "b"]) == 0.0


# --- top_pages ---------------------------------------------------------------


def test_top_pages_orders_by_score_then_page_id(top_pages) -> None:
    scores = {"b": 2.0, "a": 2.0, "c": 3.0}
    assert top_pages.top_pages(scores, 3) == ["c", "a", "b"]


def test_a_zero_scoring_page_is_never_returned_even_below_k(top_pages) -> None:
    assert top_pages.top_pages({"a": 1.0, "b": 0.0, "c": -1.0}, 5) == ["a"]


def test_k_truncates(top_pages) -> None:
    assert top_pages.top_pages({"a": 3.0, "b": 2.0, "c": 1.0}, 2) == ["a", "b"]


def test_no_scores_at_all_returns_nothing(top_pages) -> None:
    assert top_pages.top_pages({}, 5) == []


# --- page: the declared shape and the one that is built ----------------------


def test_the_declared_page_shape_matches_what_load_pages_builds(load_pages, tmp_path) -> None:
    """The `Page` TypedDict is annotation-only, so nothing checks it at runtime."""
    page = _load("page", EVAL_ROOT / "page.py")
    root = _wiki(tmp_path, {"topics/a.md": "---\ntitle: A\nsummary: S\n---\nbody"})
    built = load_pages.load_pages(root)["topics/a"]
    assert set(built) == set(page.Page.__annotations__)


# --- run: the harness that turns the baselines into two numbers ---------------


@pytest.fixture
def harness(tmp_path):
    """`run.main` pointed at a wiki and a query set built in a tmp dir."""
    module = _load("run", EVAL_ROOT / "run.py")

    def build(pages: dict[str, str], queries: str):
        root = _wiki(tmp_path, pages)
        query_file = tmp_path / "queries.toml"
        query_file.write_text(queries, encoding="utf-8")
        module.ROOT = root
        module.QUERIES = query_file
        return module

    return build


def test_the_runner_reports_both_baselines_and_exits_zero(harness, capsys) -> None:
    module = harness(
        {"topics/holded.md": "---\ntitle: Holded\n---\nthe invoicing tool"},
        '[[query]]\nquestion = "how is holded set up"\nexpected_pages = ["topics/holded"]\n',
    )
    assert module.main() == 0
    out = capsys.readouterr().out
    assert "1 questions, recall@5" in out
    assert "keyword: 1.00" in out
    assert "pagerank: 1.00" in out


def test_a_missed_question_is_printed_with_what_was_returned(harness, capsys) -> None:
    module = harness(
        {"topics/holded.md": "---\ntitle: Holded\n---\nthe invoicing tool", "topics/b.md": "b"},
        '[[query]]\nquestion = "how is holded set up"\nexpected_pages = ["topics/b"]\n',
    )
    module.main()
    out = capsys.readouterr().out
    assert "keyword missed topics/b: how is holded set up" in out
    assert "returned: topics/holded" in out
    assert "keyword: 0.00" in out


def test_a_refusal_question_the_baseline_answers_anyway_is_named(harness, capsys) -> None:
    module = harness(
        {"topics/holded.md": "---\ntitle: Holded\n---\nthe invoicing tool"},
        '[[query]]\nquestion = "how is holded set up"\nexpected_pages = []\n',
    )
    module.main()
    out = capsys.readouterr().out
    assert "(nothing should have been returned)" in out


def test_a_question_the_wiki_cannot_answer_returns_nothing(harness, capsys) -> None:
    module = harness(
        {"topics/holded.md": "---\ntitle: Holded\n---\nthe invoicing tool"},
        '[[query]]\nquestion = "cirbe deferral"\nexpected_pages = []\n',
    )
    assert module.main() == 0
    out = capsys.readouterr().out
    assert "keyword: 1.00" in out
    assert "pagerank: 1.00" in out


def test_pagerank_is_seeded_from_the_keyword_hits_not_the_whole_corpus(harness, capsys) -> None:
    """A hub linked from everywhere must not win a question about something else.

    Measured on the first real run: seeding with the full score vector returned
    the same five hubs for every question, which is what this guards.
    """
    pages = {
        "topics/hub.md": "---\ntitle: Hub\n---\n" + " ".join(f"[[topics/p{n}]]" for n in range(8))
    }
    pages.update({f"topics/p{n}.md": f"---\ntitle: P{n}\n---\ncommon word" for n in range(8)})
    pages["topics/cirbe.md"] = "---\ntitle: Cirbe\n---\nthe risk report"
    module = harness(
        pages,
        '[[query]]\nquestion = "cirbe risk report"\nexpected_pages = ["topics/cirbe"]\n',
    )
    module.main()
    out = capsys.readouterr().out
    assert "pagerank: 1.00" in out
