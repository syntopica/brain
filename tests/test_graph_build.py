"""What the graph builder actually does to a directory of wiki pages.

`tools/graph` is the wiki's only structural lint: it decides what counts as a
page, what counts as a link, which pages are orphans, which are missing from
index.md, and which unlinked pairs are worth connecting. Every one of those is
a judgment that can drift without anything failing, so they are pinned here.

Nothing in this file touches the real wiki: every case builds a small page tree
under `tmp_path` and selects it through configuration.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.tool_paths import TOOLS_ROOT
from tools.graph.parse_frontmatter import parse_frontmatter
from tools.graph.print_related import TOP_RELATED

GRAPH = TOOLS_ROOT / "graph"


def _load(name: str, path: Path) -> ModuleType:
    """Import a tool module by path, the way the tool imports its siblings."""
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
def build() -> ModuleType:
    return _load("graph_build", GRAPH / "build.py")


@pytest.fixture(scope="module")
def link_components() -> ModuleType:
    return _load("graph_link_components", GRAPH / "link_components.py")


def _write(root: Path, page_id: str, text: str) -> None:
    path = root / f"{page_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------
# frontmatter_sources: which `sources:` entries a page declares
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# parse_frontmatter: the three scalars the viewer shows
# --------------------------------------------------------------------------


def test_only_the_three_viewer_keys_are_parsed(build: ModuleType) -> None:
    text = "---\ntitle: A page\ntype: topic\nupdated: 2026-01-01\nreviewed: true\n---\n"
    assert parse_frontmatter(text) == {
        "title": "A page",
        "type": "topic",
        "updated": "2026-01-01",
    }


def test_frontmatter_values_are_unquoted(build: ModuleType) -> None:
    assert parse_frontmatter("---\ntitle: 'A page'\n---\n")["title"] == "A page"


def test_missing_or_unterminated_frontmatter_parses_to_nothing(build: ModuleType) -> None:
    assert parse_frontmatter("body only\n") == {}
    assert parse_frontmatter("---\ntitle: A\n") == {}


# --------------------------------------------------------------------------
# scan_pages: what counts as a page and what counts as a link
# --------------------------------------------------------------------------


def test_scan_reads_the_five_page_directories_and_nothing_else(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for directory in ["projects", "business", "people", "topics", "personal"]:
        _write(tmp_path, f"{directory}/p", "body\n")
    _write(tmp_path, "sources/p", "body\n")
    _write(tmp_path, "index", "[[projects/p]]\n")
    assert set(
        build.scan_pages(
            tmp_path,
            tuple(
                tmp_path / name for name in ("projects", "business", "people", "topics", "personal")
            ),
        )
    ) == {
        "projects/p",
        "business/p",
        "people/p",
        "topics/p",
        "personal/p",
    }


def test_a_page_without_frontmatter_falls_back_to_its_stem_and_directory(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "topics/llm-wiki", "body\n")
    page = build.scan_pages(
        tmp_path,
        tuple(tmp_path / name for name in ("projects", "business", "people", "topics", "personal")),
    )["topics/llm-wiki"]
    assert page["title"] == "llm-wiki"
    assert page["type"] == "topic"
    assert page["updated"] == ""


def test_the_business_directory_defaults_to_a_misspelt_type(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Today's behaviour, recorded rather than fixed: see the report.

    The fallback is `d.rstrip("s")`, which strips *every* trailing `s` rather
    than one, so a business page with no explicit `type:` is typed `busine`.
    The viewer filters on this value.
    """
    _write(tmp_path, "business/holded", "body\n")
    assert (
        build.scan_pages(
            tmp_path,
            tuple(
                tmp_path / name for name in ("projects", "business", "people", "topics", "personal")
            ),
        )["business/holded"]["type"]
        == "busine"
    )


def test_root_references_without_a_directory_are_not_links(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "topics/a", "see [[SCHEMA]] and [[index]] and [[topics/b]]\n")
    assert build.scan_pages(
        tmp_path,
        tuple(tmp_path / name for name in ("projects", "business", "people", "topics", "personal")),
    )["topics/a"]["targets"] == ["topics/b"]


def test_links_inside_code_spans_are_not_links(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "topics/a", "write `[[topics/b]]` to link, like [[topics/c]]\n")
    assert build.scan_pages(
        tmp_path,
        tuple(tmp_path / name for name in ("projects", "business", "people", "topics", "personal")),
    )["topics/a"]["targets"] == ["topics/c"]


def test_an_alias_or_anchor_is_stripped_from_the_target(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "topics/a", "[[topics/b|the other page]] and [[topics/c#section]]\n")
    assert build.scan_pages(
        tmp_path,
        tuple(tmp_path / name for name in ("projects", "business", "people", "topics", "personal")),
    )["topics/a"]["targets"] == ["topics/b", "topics/c"]


def test_repeated_links_survive_the_scan(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deduplication is the caller's decision; the scan reports occurrences."""
    _write(tmp_path, "topics/a", "[[topics/b]] then again [[topics/b]]\n")
    assert build.scan_pages(
        tmp_path,
        tuple(tmp_path / name for name in ("projects", "business", "people", "topics", "personal")),
    )["topics/a"]["targets"] == ["topics/b", "topics/b"]


def test_a_link_in_the_frontmatter_is_not_a_link(
    build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "topics/a", "---\ntitle: '[[topics/b]]'\n---\nbody\n")
    assert (
        build.scan_pages(
            tmp_path,
            tuple(
                tmp_path / name for name in ("projects", "business", "people", "topics", "personal")
            ),
        )["topics/a"]["targets"]
        == []
    )


# --------------------------------------------------------------------------
# build_nodes / undirected_neighbours: the degrees the viewer draws
# --------------------------------------------------------------------------


def _page(page_id: str, targets: list[str], page_type: str = "topic") -> dict[str, object]:
    directory, _, stem = page_id.partition("/")
    return {
        "id": page_id,
        "dir": directory,
        "title": stem,
        "type": page_type,
        "updated": "",
        "sources": set(),
        "targets": targets,
    }


def test_outbound_counts_distinct_existing_pages_only(build: ModuleType) -> None:
    """A repeat, a self-link and a dangling target must all count for nothing."""
    pages = {
        "topics/a": _page("topics/a", ["topics/b", "topics/b", "topics/a", "topics/gone"]),
        "topics/b": _page("topics/b", []),
    }
    nodes = {
        n["id"]: n for n in build.build_nodes(pages, {"topics/a": [], "topics/b": ["topics/a"]})
    }
    assert nodes["topics/a"]["out"] == 1
    assert nodes["topics/b"]["in"] == 1
    assert nodes["topics/a"]["in"] == 0


def test_neighbours_are_symmetric(build: ModuleType) -> None:
    pages = {"topics/a": _page("topics/a", []), "topics/b": _page("topics/b", [])}
    neighbours = build.undirected_neighbours(pages, [["topics/a", "topics/b"]])
    assert neighbours == {"topics/a": {"topics/b"}, "topics/b": {"topics/a"}}


def test_a_page_no_link_touches_still_gets_an_entry(build: ModuleType) -> None:
    pages = {"topics/a": _page("topics/a", [])}
    assert build.undirected_neighbours(pages, []) == {"topics/a": set()}


# --------------------------------------------------------------------------
# link_components: clusters the orphan count cannot show
# --------------------------------------------------------------------------


def test_one_cluster_is_reported_as_one_component(link_components: ModuleType) -> None:
    neighbours = {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}
    assert link_components.link_components(neighbours) == [["a", "b", "c"]]


def test_a_closed_cluster_with_no_orphans_is_still_a_second_component(
    link_components: ModuleType,
) -> None:
    neighbours = {"a": {"b"}, "b": {"a"}, "x": {"y", "z"}, "y": {"x", "z"}, "z": {"x", "y"}}
    assert link_components.link_components(neighbours) == [["x", "y", "z"], ["a", "b"]]


def test_an_isolated_page_is_its_own_component(link_components: ModuleType) -> None:
    assert link_components.link_components({"a": set()}) == [["a"]]


def test_equal_sized_components_are_ordered_by_their_first_member(
    link_components: ModuleType,
) -> None:
    neighbours = {"m": {"n"}, "n": {"m"}, "a": {"b"}, "b": {"a"}}
    assert link_components.link_components(neighbours) == [["a", "b"], ["m", "n"]]


# --------------------------------------------------------------------------
# related_pairs: the cross-links the wiki should have
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# main: the report, end to end, over a wiki built in tmp_path
# --------------------------------------------------------------------------


@pytest.fixture
def wiki(build: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A configured wiki carrying every defect main is meant to name."""
    data = make_data_directory(
        tmp_path,
        {
            "topics/a.md": "---\ntitle: A\ntype: topic\n---\n[[topics/b]] [[topics/gone]]\n",
            "topics/b.md": "---\ntitle: B\ntype: topic\n---\n[[topics/b]]\n",
            "projects/lonely.md": "---\ntitle: Lonely\ntype: project\n---\nno links\n",
        },
    )
    wiki = data / "brain"
    _write(wiki, "index", "[[topics/a]] [[topics/b]] [[topics/nowhere]]\n")
    monkeypatch.chdir(data)
    monkeypatch.delenv("SYNTOPICA_DATA", raising=False)
    return wiki


def test_main_reports_every_defect_and_returns_zero(
    build: ModuleType, wiki: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert build.main([]) == 0
    out = capsys.readouterr().out
    assert "pages 3  links 1  orphans 2  dangling 1  unindexed 1" in out
    assert "dangling: topics/a -> [[topics/gone]]" in out
    assert "self-link: topics/b" in out
    assert "index.md links nowhere: [[topics/nowhere]]" in out
    assert "not in index.md: projects/lonely (linked from nothing)" in out
    assert "links to no other page: projects/lonely" in out
    assert "cluster reachable from nothing else: projects/lonely" in out


def test_main_writes_the_viewer_with_the_data_substituted(build: ModuleType, wiki: Path) -> None:
    build.main([])
    written = (wiki / "graph.html").read_text(encoding="utf-8")
    assert "/*__DATA__*/" not in written
    assert '"topics/a"' in written
    assert "<" in written  # the viewer template, not a bare JSON dump


def test_an_unindexed_page_names_who_does_link_to_it(
    build: ModuleType, wiki: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(wiki, "topics/a", "---\ntitle: A\n---\n[[projects/lonely]] [[topics/gone]]\n")
    build.main([])
    assert "not in index.md: projects/lonely (linked from topics/a)" in capsys.readouterr().out


def test_a_wiki_with_no_pages_at_all_still_reports(
    build: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The failure path a fresh checkout hits: no page directories exist yet."""
    data = make_data_directory(tmp_path, {})
    assert build.main(["--data", str(data)]) == 0
    assert "pages 0  links 0  orphans 0  dangling 0  unindexed 0" in capsys.readouterr().out


def test_the_related_tail_is_counted_rather_than_printed(
    build: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Above TOP_RELATED the report switches to a count with its floor named."""
    shared = "---\ntype: topic\nsources:\n  - https://s\n---\nbody\n"
    data = make_data_directory(tmp_path, {f"topics/p{i}.md": shared for i in range(6)})
    build.main(["--data", str(data)])
    out = capsys.readouterr().out
    # 15 unlinked pairs, all scoring 5.0: ten printed, five counted.
    assert out.count("related but unlinked") == TOP_RELATED
    assert "... and 5 more scoring above 1.0, down to 5.0" in out


def test_graph_writes_into_data_directory(tmp_path: Path) -> None:
    from tests.fixtures.make_data_directory import make_data_directory
    from tools.graph.build import main

    data = make_data_directory(tmp_path)
    output = GRAPH / "graph.html"
    before = output.stat() if output.exists() else None
    assert main(["--data", str(data)]) == 0
    assert (data / "brain/graph.html").is_file()
    assert (output.stat() if output.exists() else None) == before


def test_graph_cli_works_from_unrelated_directory(tmp_path: Path) -> None:
    import subprocess

    from tests.fixtures.make_data_directory import make_data_directory

    data = make_data_directory(tmp_path)
    result = subprocess.run(
        [sys.executable, str(GRAPH / "build.py"), "--data", str(data)],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (data / "brain/graph.html").is_file()


def test_graph_without_data_from_tmp_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    monkeypatch.delenv("SYNTOPICA_DATA", raising=False)
    result = subprocess.run(
        [sys.executable, str(GRAPH / "build.py")],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "syntopica.config.json" in result.stderr


def test_graph_refuses_output_symlink_outside_data(tmp_path: Path) -> None:
    from tools.graph.build import main

    data = make_data_directory(tmp_path)
    outside = tmp_path / "outside.html"
    outside.write_text("Keep this file.", encoding="utf-8")
    (data / "brain/graph.html").symlink_to(outside)
    assert main(["--data", str(data)]) == 1
    assert outside.read_text(encoding="utf-8") == "Keep this file."


def test_graph_resolves_environment_data_from_tmp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.graph.build import main

    data = make_data_directory(tmp_path)
    monkeypatch.setenv("SYNTOPICA_DATA", str(data))
    monkeypatch.chdir("/tmp")
    assert main([]) == 0
    assert (data / "brain/graph.html").is_file()
