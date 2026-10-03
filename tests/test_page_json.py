"""`brain page --json --id` reads one page, only from inside a page root."""

import json
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.tree_snapshot import tree_snapshot
from tools.index.brain_cli import brain_cli
from tools.index.page_document import BODY_CAP

PAGE = (
    "---\ntitle: A\ntype: note\nupdated: 2026-01-01\nsummary: 'A page.'\n"
    "sources:\n  - https://example.test/s\n---\n"
)


def _page(
    data: Path, page_id: str, capsys: pytest.CaptureFixture[str]
) -> tuple[int, dict[str, Any]]:
    status = brain_cli(["--data", str(data), "page", "--json", "--id", page_id])
    return status, json.loads(capsys.readouterr().out)


def test_page_document_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(
        tmp_path,
        {
            "notes/a.md": PAGE + "Body with [[notes/b]], [[b]] and [[notes/absent]].\n",
            "notes/b.md": PAGE + "Back to [[notes/a]].\n",
        },
    )
    before = tree_snapshot(tmp_path)
    status, document = _page(data, "notes/a", capsys)
    assert status == 0
    assert document == {
        "schemaVersion": 1,
        "id": "notes/a",
        "frontmatter": {
            "title": "A",
            "type": "note",
            "updated": "2026-01-01",
            "summary": "A page.",
            "sources": ["https://example.test/s"],
        },
        "body": "Body with [[notes/b]], [[b]] and [[notes/absent]].\n",
        "truncated": False,
        "links": {
            "outbound": [
                {"target": "notes/b", "exists": True},
                {"target": "notes/absent", "exists": False},
            ],
            "inbound": ["notes/b"],
        },
    }
    assert tree_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "page_id",
    ["", "/etc/passwd", "notes", "notes/.hidden", "notes\\a", "notes/a\0"],
)
def test_malformed_ids_are_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], page_id: str
) -> None:
    data = make_data_directory(tmp_path, {"notes/a.md": PAGE})
    assert _page(data, page_id, capsys) == (1, {"schemaVersion": 1, "error": "invalid_page_id"})


@pytest.mark.parametrize(
    "page_id", ["notes/..", "../notes/a", "notes/../notes/a", "../../data/syntopica.config", "x/a"]
)
def test_traversal_matches_no_root(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], page_id: str
) -> None:
    data = make_data_directory(tmp_path, {"notes/a.md": PAGE})
    status, document = _page(data, page_id, capsys)
    assert status == 1
    assert document["error"] in {"invalid_page_id", "page_not_found"}
    assert "body" not in document


def test_symlink_escaping_the_root_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = make_data_directory(tmp_path, {"notes/a.md": PAGE})
    secret = tmp_path / "secret.md"
    secret.write_text(PAGE + "Outside the roots.\n", encoding="utf-8")
    (data / "brain/notes/leak.md").symlink_to(secret)
    status, document = _page(data, "notes/leak", capsys)
    assert (status, document) == (1, {"schemaVersion": 1, "error": "page_not_found"})


def test_symlink_inside_the_root_is_followed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = make_data_directory(tmp_path, {"notes/a.md": PAGE + "Inside.\n"})
    (data / "brain/notes/alias.md").symlink_to(data / "brain/notes/a.md")
    status, document = _page(data, "notes/alias", capsys)
    assert status == 0
    assert document["body"] == "Inside.\n"


def test_body_is_capped(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(tmp_path, {"notes/a.md": PAGE + "é" * BODY_CAP})
    status, document = _page(data, "notes/a", capsys)
    assert status == 0
    assert document["truncated"] is True
    assert len(document["body"].encode("utf-8")) <= BODY_CAP
    assert "�" not in document["body"]


def test_page_without_frontmatter(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(tmp_path, {"notes/a.md": "Plain text.\n"})
    status, document = _page(data, "notes/a", capsys)
    assert status == 0
    assert document["frontmatter"] == {"sources": []}
    assert document["body"] == "Plain text.\n"


def test_page_requires_json_and_id(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    for argv in (["page", "--id", "notes/example"], ["page", "--json"]):
        with pytest.raises(SystemExit):
            brain_cli(["--data", str(data), *argv])
