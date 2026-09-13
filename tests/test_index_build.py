"""The generator that owns index.md: what it reads out of a page and what it writes.

`tools/index/build.py` is the only writer of the root map, and `--check` is a
gate other sessions run. Both halves are easy to break silently: the reader
folds a `summary:` prettier has wrapped, and the comparison is deliberately
whitespace-blind so a reflow does not read as a stale map. Neither had a test.

Everything here works on a configured synthetic wiki under tmp_path.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.tool_paths import TOOLS_ROOT
from tools.index.raw_summary import raw_summary
from tools.index.rendered import FOOTER, HEADER
from tools.index.summary_of import summary_of


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
def build():
    return _load("index_build", TOOLS_ROOT / "index" / "build.py")


@pytest.fixture
def wiki(build, tmp_path, monkeypatch):
    """A configured synthetic wiki with one section and no index yet."""
    data = make_data_directory(tmp_path, {"topics/seed.md": "placeholder"})
    wiki = data / "brain"
    (wiki / "topics/seed.md").unlink()
    (wiki / "index.md").unlink()
    monkeypatch.chdir(data)
    monkeypatch.delenv("SYNTOPICA_DATA", raising=False)
    return wiki


def _page(root: Path, page_id: str, frontmatter: str) -> Path:
    path = root / "topics" / f"{page_id}.md"
    path.write_text(f"---\n{frontmatter}\n---\n\nbody\n", encoding="utf-8")
    return path


# --- raw_summary: reading a value prettier may have wrapped -----------------


def test_a_summary_on_its_key_line_is_read_as_written(build) -> None:
    assert raw_summary("title: x\nsummary: 'one line'\ntype: topic") == "'one line'"


def test_a_summary_wrapped_onto_following_lines_is_joined_with_one_space(build) -> None:
    block = "summary: 'a summary long enough\n  that prettier wrapped it'\ntype: topic"
    assert raw_summary(block) == "'a summary long enough that prettier wrapped it'"


def test_a_summary_that_starts_below_its_key_is_still_found(build) -> None:
    block = "title: x\nsummary:\n  'the whole value\n  lives down here'\ntype: topic"
    assert raw_summary(block) == "'the whole value lives down here'"


def test_the_next_column_zero_key_ends_the_value(build) -> None:
    block = "summary: 'mine'\nsources:\n  - not/mine.md"
    assert raw_summary(block) == "'mine'"


def test_an_indented_summary_key_is_not_a_summary(build) -> None:
    assert raw_summary("contradictions:\n  summary: 'nested'") == ""


def test_a_block_with_no_summary_key_reads_as_empty(build) -> None:
    assert raw_summary("title: x\ntype: topic") == ""


def test_a_blank_line_truncates_a_folded_summary(build) -> None:
    """Today's behaviour, and a defect: YAML folds across a blank line.

    The reader stops at the first line that is not indented, and an empty line
    is not indented, so the half below it is dropped without a word. Recorded
    rather than fixed - summaries are one line by convention, so no page hits
    this today.
    """
    assert raw_summary("summary: 'first half\n\n  second half'") == "'first half"


# --- summary_of: frontmatter framing and YAML quoting ----------------------


def test_a_single_quoted_summary_loses_its_quotes(build, wiki) -> None:
    assert summary_of(_page(wiki, "p", "summary: 'plain'")) == "plain"


def test_a_doubled_quote_inside_a_single_quoted_summary_becomes_one(build, wiki) -> None:
    assert summary_of(_page(wiki, "p", "summary: 'It''s here'")) == "It's here"


def test_a_double_quoted_summary_loses_its_quotes_but_keeps_its_escapes(build, wiki) -> None:
    """Today's behaviour: `\\"` is not decoded, unlike YAML.

    Harmless while SCHEMA.md asks for single quotes, and left alone because
    changing it would change what index.md says.
    """
    page = _page(wiki, "p", 'summary: "a \\"quoted\\" word"')
    assert summary_of(page) == 'a \\"quoted\\" word'


def test_an_unquoted_summary_is_taken_verbatim(build, wiki) -> None:
    assert summary_of(_page(wiki, "p", "summary: bare words")) == "bare words"


def test_a_page_with_no_frontmatter_has_no_summary(build, wiki) -> None:
    page = wiki / "topics" / "p.md"
    page.write_text("# Heading\n\nsummary: 'not frontmatter'\n", encoding="utf-8")
    assert summary_of(page) == ""


def test_frontmatter_that_is_never_closed_has_no_summary(build, wiki) -> None:
    page = wiki / "topics" / "p.md"
    page.write_text("---\nsummary: 'orphan'\n", encoding="utf-8")
    assert summary_of(page) == ""


# --- rendered: the map itself ----------------------------------------------


def test_pages_are_listed_alphabetically_by_id_with_their_summary(build, wiki) -> None:
    _page(wiki, "zebra", "summary: 'last'")
    _page(wiki, "alpha", "summary: 'first'")
    body = build.rendered(wiki, (wiki / "topics",))
    assert "- [[topics/alpha]] — first" in body
    assert "- [[topics/zebra]] — last" in body
    assert body.index("topics/alpha") < body.index("topics/zebra")


def test_a_page_without_a_summary_is_still_listed_and_named_on_stderr(build, wiki, capsys) -> None:
    _page(wiki, "silent", "title: Silent")
    body = build.rendered(wiki, (wiki / "topics",))
    assert "- [[topics/silent]]\n" in body
    assert "—" not in body.split("## Topics")[1]
    assert "no summary: topics/silent" in capsys.readouterr().err


def test_the_header_and_the_inbox_footer_are_constants_not_data(build, wiki) -> None:
    body = build.rendered(wiki, (wiki / "topics",))
    assert body.startswith(HEADER)
    assert body.endswith(FOOTER)


def test_a_section_whose_folder_is_empty_still_gets_its_heading(build, wiki) -> None:
    assert "## Topics" in build.rendered(wiki, (wiki / "topics",))


# --- normalized: why --check does not fire on a reflow ---------------------


def test_rewrapping_a_bullet_does_not_change_the_normalized_form(build) -> None:
    one_line = "- [[topics/a]] — a summary long enough to wrap"
    wrapped = "- [[topics/a]] —\n  a summary long enough\n  to wrap"
    assert build.normalized(one_line) == build.normalized(wrapped)


def test_changing_a_word_does_change_the_normalized_form(build) -> None:
    assert build.normalized("- [[topics/a]] — one") != build.normalized("- [[topics/a]] — two")


# --- main: argument handling and exit status -------------------------------


def test_writing_creates_the_index_and_reports_the_page_count(build, wiki, capsys) -> None:
    _page(wiki, "alpha", "summary: 'first'")
    _page(wiki, "beta", "summary: 'second'")
    sys_argv, sys.argv = sys.argv, ["build.py"]
    try:
        assert build.main() == 0
    finally:
        sys.argv = sys_argv
    assert "- [[topics/alpha]] — first" in (wiki / "index.md").read_text(encoding="utf-8")
    assert "index.md: 2 pages" in capsys.readouterr().out


def test_check_leaves_the_file_alone_and_exits_zero_when_it_matches(build, wiki) -> None:
    _page(wiki, "alpha", "summary: 'first'")
    (wiki / "index.md").write_text(build.rendered(wiki, (wiki / "topics",)), encoding="utf-8")
    before = (wiki / "index.md").read_text(encoding="utf-8")
    sys_argv, sys.argv = sys.argv, ["build.py", "--check"]
    try:
        assert build.main() == 0
    finally:
        sys.argv = sys_argv
    assert (wiki / "index.md").read_text(encoding="utf-8") == before


def test_check_exits_one_and_writes_nothing_when_a_page_is_missing(build, wiki, capsys) -> None:
    _page(wiki, "alpha", "summary: 'first'")
    (wiki / "index.md").write_text(build.rendered(wiki, (wiki / "topics",)), encoding="utf-8")
    _page(wiki, "beta", "summary: 'added since'")
    sys_argv, sys.argv = sys.argv, ["build.py", "--check"]
    try:
        assert build.main() == 1
    finally:
        sys.argv = sys_argv
    assert "topics/beta" not in (wiki / "index.md").read_text(encoding="utf-8")
    assert "index.md is out of date" in capsys.readouterr().err


def test_check_accepts_an_index_prettier_has_reflowed(build, wiki) -> None:
    _page(wiki, "alpha", "summary: 'a summary long enough that prettier wraps the bullet'")
    reflowed = build.rendered(wiki, (wiki / "topics",)).replace(" — ", " —\n  ")
    (wiki / "index.md").write_text(reflowed, encoding="utf-8")
    sys_argv, sys.argv = sys.argv, ["build.py", "--check"]
    try:
        assert build.main() == 0
    finally:
        sys.argv = sys_argv


def test_check_raises_when_the_index_does_not_exist(build, wiki) -> None:
    """Today's behaviour, and a defect: a missing index.md is a traceback.

    `--check` reads index.md before comparing, so on a checkout that has none
    the gate dies with FileNotFoundError instead of the "run
    python3 tools/index/build.py" line that is the whole point of the mode.
    Recorded, not fixed: fixing it changes what the gate prints.
    """
    _page(wiki, "alpha", "summary: 'first'")
    sys_argv, sys.argv = sys.argv, ["build.py", "--check"]
    try:
        with pytest.raises(FileNotFoundError):
            build.main()
    finally:
        sys.argv = sys_argv


def test_an_unknown_flag_is_rejected_without_writing(build, wiki) -> None:
    """Reject misspelled options rather than accidentally writing the index."""
    _page(wiki, "alpha", "summary: 'first'")
    sys_argv, sys.argv = sys.argv, ["build.py", "--dry-run"]
    try:
        with pytest.raises(SystemExit) as error:
            build.main()
        assert error.value.code == 2
    finally:
        sys.argv = sys_argv
    assert not (wiki / "index.md").exists()


def test_index_check_reads_selected_data_directory(tmp_path: Path) -> None:
    from tests.fixtures.make_data_directory import make_data_directory
    from tools.index.build import main

    data = make_data_directory(tmp_path)
    assert main(["--data", str(data), "--check"]) == 0


def test_index_cli_works_from_unrelated_directory(tmp_path: Path) -> None:
    import subprocess

    from tests.fixtures.make_data_directory import make_data_directory

    data = make_data_directory(tmp_path)
    result = subprocess.run(
        [sys.executable, str(TOOLS_ROOT / "index/build.py"), "--data", str(data), "--check"],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_index_without_data_from_tmp_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    monkeypatch.delenv("SYNTOPICA_DATA", raising=False)
    result = subprocess.run(
        [sys.executable, str(TOOLS_ROOT / "index/build.py"), "--check"],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "syntopica.config.json" in result.stderr
