"""`brain find` answers where in the wiki a question is already answered.

The command exists because the alternative a session reaches for is `grep -r`,
which walks whatever sits beside the pages. Nothing here touches a real wiki:
every case builds a page tree under `tmp_path` and selects it through
configuration.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from tests.fixtures.make_data_directory import make_data_directory
from tests.tool_paths import TOOLS_ROOT
from tools.find.matching_section import matching_section

_PAGES = {
    "notes/invoices.md": (
        "---\ntitle: Invoices\nsummary: How invoices are collected.\n---\n\n"
        "## Collecting\n\nThe collector reads every invoice from the portal.\n\n"
        "## Filing\n\nFiled invoices move to the archive. See [[notes/archive]].\n"
    ),
    "notes/archive.md": (
        "---\ntitle: Archive\nsummary: Where filed material lives.\n---\n\n"
        "Cold storage for anything already filed. See [[notes/invoices]].\n"
    ),
}


def _command() -> ModuleType:
    """Import the entrypoint the way `brain find` runs it."""
    path = TOOLS_ROOT / "find/build.py"
    spec = importlib.util.spec_from_file_location("find_build", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(TOOLS_ROOT / "eval"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def test_find_names_the_page_and_the_line_that_carries_the_words(tmp_path: Path, capsys) -> None:
    root = make_data_directory(tmp_path, _PAGES)
    assert _command().main(["--data", str(root), "--json", "collecting", "invoice"]) == 0
    hits = __import__("json").loads(capsys.readouterr().out)["hits"]
    assert hits[0]["page"].endswith("notes/invoices.md")
    assert hits[0]["heading"] == "## Collecting"
    assert hits[0]["line"] > 0
    assert "invoice" in hits[0]["text"].lower()


def test_find_says_so_rather_than_printing_nothing(tmp_path: Path, capsys) -> None:
    """An empty result is an answer about the wiki, and must read as one."""
    root = make_data_directory(tmp_path, _PAGES)
    assert _command().main(["--data", str(root), "zzzqqq"]) == 0
    assert "No page carries" in capsys.readouterr().out


def test_the_section_is_the_heading_above_the_match_not_the_first_one() -> None:
    body = "## One\n\nnothing here\n\n## Two\n\nthe answer is here\n"
    assert matching_section(body, ["answer"]) == ("## Two", 7, "the answer is here")


def test_a_line_carrying_two_terms_beats_an_earlier_line_carrying_one() -> None:
    body = "alpha alone\nalpha and beta together\n"
    assert matching_section(body, ["alpha", "beta"])[1] == 2


def test_a_configured_directory_is_a_path_not_a_name(tmp_path: Path, capsys) -> None:
    """A name is not a location, and the wrong location here is the archive.

    Reducing a configured `curated/captures` to `captures` resolved it against
    the data root, where a real instance keeps its capture archive: the command
    then searched the very directory it exists to stay out of (reproduced by
    review, 2026-09-16).
    """
    root = make_data_directory(
        tmp_path,
        {
            "curated/captures/page.md": (
                "---\ntitle: Curated\nsummary: A curated page.\n---\n\nCuratedanswer lives here.\n"
            )
        },
    )
    (root / "brain/captures").mkdir(parents=True, exist_ok=True)
    (root / "brain/captures/raw.md").write_text(
        "---\ntitle: Raw\nsummary: A capture.\n---\n\nArchiveonly raw content.\n"
    )
    assert _command().main(["--data", str(root), "--json", "archiveonly"]) == 0
    assert __import__("json").loads(capsys.readouterr().out)["hits"] == []


def test_the_line_number_is_the_one_the_file_has(tmp_path: Path, capsys) -> None:
    """Counting from the body reported 67 for a line at 86 on the live wiki."""
    root = make_data_directory(tmp_path, _PAGES)
    assert _command().main(["--data", str(root), "--json", "filed", "archive"]) == 0
    hit = __import__("json").loads(capsys.readouterr().out)["hits"][0]
    lines = Path(hit["page"]).read_text().splitlines()
    assert lines[hit["line"] - 1].strip() == hit["text"]


def test_a_heading_and_a_summary_can_themselves_be_the_match() -> None:
    """A page ranked on its summary alone used to cite line 0 with no text."""
    text = "---\ntitle: T\nsummary: The collector reads the portal.\n---\n\n## Filing\n\nbody\n"
    assert matching_section(text, ["collector"]) == (
        "",
        3,
        "summary: The collector reads the portal.",
    )
    assert matching_section(text, ["filing"]) == ("## Filing", 6, "## Filing")
