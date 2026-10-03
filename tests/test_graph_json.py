"""`brain graph --json` prints the graph and writes nothing at all."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.tool_paths import TOOLS_ROOT
from tests.tree_snapshot import tree_snapshot
from tools.graph.build import main

ROOT = TOOLS_ROOT.parent
PAGE = "---\ntitle: Private title\ntype: {kind}\nupdated: 2026-01-01\nsummary: S.\n---\n{body}\n"
PAGES = {
    "notes/a.md": PAGE.format(kind="note", body="[[notes/b]] [[notes/b]] [[notes/absent]]"),
    "notes/b.md": PAGE.format(kind="note", body="[[notes/b]]"),
    "notes/c.md": PAGE.format(kind="topic", body="nothing"),
}


def _graph(argv: list[str], capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    assert main(argv) == 0
    document: dict[str, object] = json.loads(capsys.readouterr().out)
    return document


def test_graph_document_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(tmp_path, PAGES)
    document = _graph(["--data", str(data), "--json", "--no-html"], capsys)
    assert document == {
        "schemaVersion": 1,
        "nodes": [
            {"id": "notes/a", "type": "note", "degree": 1},
            {"id": "notes/b", "type": "note", "degree": 1},
            {"id": "notes/c", "type": "topic", "degree": 0},
        ],
        "edges": [{"source": "notes/a", "target": "notes/b"}],
        "orphans": ["notes/a", "notes/c"],
        "dangling": [{"page": "notes/a", "target": "notes/absent"}],
    }
    assert "Private title" not in json.dumps(document)


def test_graph_json_writes_nothing_through_the_cli(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path, PAGES)
    before = tree_snapshot(tmp_path)
    result = subprocess.run(
        [str(ROOT / "bin/brain"), "--data", str(data), "graph", "--json", "--no-html"],
        cwd="/tmp",
        env={k: v for k, v in os.environ.items() if k != "SYNTOPICA_DATA"},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["schemaVersion"] == 1
    assert tree_snapshot(tmp_path) == before
    assert not (data / "brain/graph.html").exists()


def test_graph_json_ignores_an_unsafe_output_it_would_never_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = make_data_directory(tmp_path, PAGES)
    outside = tmp_path / "outside.html"
    outside.write_text("Keep this file.", encoding="utf-8")
    (data / "brain/graph.html").symlink_to(outside)
    _graph(["--data", str(data), "--json", "--no-html"], capsys)
    assert outside.read_text(encoding="utf-8") == "Keep this file."


def test_related_pairs_are_limited(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    shared = "---\ntype: topic\nsources:\n  - https://s\n---\nbody\n"
    data = make_data_directory(tmp_path, {f"topics/p{i}.md": shared for i in range(6)})
    before = tree_snapshot(tmp_path)
    document = _graph(["--data", str(data), "--json", "--related", "--limit", "3"], capsys)
    assert document["schemaVersion"] == 1
    assert document["total"] == 15
    assert document["pairs"] == [
        {"left": "topics/p0", "right": "topics/p1", "score": 5.0},
        {"left": "topics/p0", "right": "topics/p2", "score": 5.0},
        {"left": "topics/p0", "right": "topics/p3", "score": 5.0},
    ]
    assert tree_snapshot(tmp_path) == before


@pytest.mark.parametrize("argv", [["--related"], ["--json", "--limit", "0"]])
def test_graph_rejects_inconsistent_flags(tmp_path: Path, argv: list[str]) -> None:
    data = make_data_directory(tmp_path, PAGES)
    with pytest.raises(SystemExit):
        main(["--data", str(data), *argv])


def test_no_html_text_report_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = make_data_directory(tmp_path, PAGES)
    before = tree_snapshot(tmp_path)
    assert main(["--data", str(data), "--no-html"]) == 0
    out = capsys.readouterr().out
    assert "dangling: notes/a -> [[notes/absent]]" in out
    assert "wrote" not in out
    assert tree_snapshot(tmp_path) == before


def test_graph_without_flags_still_writes_html(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path, PAGES)
    assert main(["--data", str(data)]) == 0
    assert (data / "brain/graph.html").is_file()
