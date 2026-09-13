"""The public lint command checks a synthetic wiki without changing it."""

from pathlib import Path

from tests.fixtures.make_data_directory import make_data_directory
from tools.index.brain_lint import brain_lint
from tools.index.load_syntopica_config import load_syntopica_config


def test_lint_accepts_coherent_wiki_without_writing_graph(tmp_path: Path) -> None:
    root = make_data_directory(tmp_path)
    config = load_syntopica_config(root, {})
    before = config.index.read_text()
    assert brain_lint(config) == 0
    assert config.index.read_text() == before
    assert not config.index.with_name("graph.html").exists()


def test_lint_rejects_dangling_links(tmp_path: Path) -> None:
    root = make_data_directory(
        tmp_path, {"notes/a.md": "---\nsummary: Example\n---\n[[notes/absent]]\n"}
    )
    assert brain_lint(load_syntopica_config(root, {})) == 1


def test_lint_rejects_stale_index(tmp_path: Path) -> None:
    root = make_data_directory(tmp_path)
    config = load_syntopica_config(root, {})
    config.index.write_text("stale\n")
    assert brain_lint(config) == 1
