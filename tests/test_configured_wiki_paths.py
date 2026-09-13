"""Independent configured index locations and graph output ownership."""

import json
from pathlib import Path

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tools.graph.build import main as graph_main
from tools.index.build import main as index_main


def test_index_and_graph_accept_pages_outside_index_parent(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    path = data / "syntopica.config.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["brain"]["index"] = "output/map.md"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert index_main(["--data", str(data)]) == 0
    assert index_main(["--data", str(data), "--check"]) == 0
    assert "[[../brain/notes/example]]" in (data / "output/map.md").read_text(encoding="utf-8")
    assert graph_main(["--data", str(data)]) == 0
    assert (data / "output/graph.html").is_file()
    assert not (data / "brain/graph.html").exists()


@pytest.mark.parametrize("target", ["index.md", "notes/example.md"])
def test_graph_never_follows_symlinks_to_input(tmp_path: Path, target: str) -> None:
    data = make_data_directory(tmp_path)
    destination = data / "brain" / target
    before = destination.read_bytes()
    (data / "brain/graph.html").symlink_to(destination)
    assert graph_main(["--data", str(data)]) == 1
    assert destination.read_bytes() == before


def test_graph_cannot_replace_a_configured_index_named_graph_html(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    path = data / "syntopica.config.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["brain"]["index"] = "brain/graph.html"
    path.write_text(json.dumps(document), encoding="utf-8")
    destination = data / "brain/graph.html"
    destination.write_text("Keep the index.", encoding="utf-8")
    assert graph_main(["--data", str(data)]) == 1
    assert destination.read_text(encoding="utf-8") == "Keep the index."
