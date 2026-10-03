"""`brain lint --json` reports fixed codes and index staleness, never messages."""

import json
from pathlib import Path

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.tree_snapshot import tree_snapshot
from tools.index.brain_cli import brain_cli

GOOD = "---\ntitle: A\ntype: note\nupdated: 2026-01-01\nsummary: A page.\n---\n"


def _lint(data: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    assert brain_cli(["--data", str(data), "lint", "--json"]) == 0
    document: dict[str, object] = json.loads(capsys.readouterr().out)
    return document


def test_clean_wiki_has_no_issues(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(tmp_path)
    before = tree_snapshot(tmp_path)
    document = _lint(data, capsys)
    assert document == {"schemaVersion": 1, "pageCount": 1, "indexStale": False, "issues": []}
    assert tree_snapshot(tmp_path) == before


def test_each_finding_has_its_fixed_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = make_data_directory(
        tmp_path,
        {
            "notes/dangling.md": GOOD + "[[notes/absent]] and [[notes/gone]]\n",
            "notes/Bad_Name.md": GOOD,
            "notes/unclosed.md": "---\ntitle: A\n",
            "notes/incomplete.md": "---\ntitle: A\n---\n",
        },
    )
    document = _lint(data, capsys)
    assert document["issues"] == [
        {"page": "notes/Bad_Name", "code": "filename_not_kebab_case"},
        {"page": "notes/dangling", "code": "dangling_link"},
        {"page": "notes/incomplete", "code": "frontmatter_incomplete"},
        {"page": "notes/unclosed", "code": "frontmatter_unclosed"},
    ]
    assert "absent" not in json.dumps(document)


def test_stale_index_is_a_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(tmp_path)
    (data / "brain/index.md").write_text("stale\n", encoding="utf-8")
    assert _lint(data, capsys)["indexStale"] is True


def test_text_lint_is_unchanged(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(tmp_path, {"notes/a.md": GOOD + "[[notes/absent]]\n"})
    assert brain_cli(["--data", str(data), "lint"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "dangling: notes/a -> [[notes/absent]]",
        "lint: 1 pages, 1 issues",
    ]


def test_lint_rejects_any_other_argument(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    with pytest.raises(SystemExit):
        brain_cli(["--data", str(data), "lint", "--json", "--verbose"])
