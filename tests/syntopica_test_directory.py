"""Build four isolated repositories for configuration tests."""

from __future__ import annotations

import json
from pathlib import Path

from tests.syntopica_git import syntopica_git


def syntopica_test_directory(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    """Create synthetic data, archive and engine roots without any commits."""
    root = tmp_path / "data"
    for path in (root, root / "clips", tmp_path / "engine-brain", tmp_path / "engine-clips"):
        path.mkdir(parents=True, exist_ok=True)
        syntopica_git(path, "init", "-q")
    document: dict[str, object] = {
        "schemaVersion": 1,
        "instanceId": "fixture",
        "brain": {
            "pages": ["brain/notes"],
            "sources": "brain/captures",
            "index": "brain/index.md",
            "ledger": "brain/.ingest",
        },
        "engines": {
            "brain": {"path": "../engine-brain", "apiVersion": 1},
            "clips": {"path": "../engine-clips", "apiVersion": 1},
        },
    }
    (root / "syntopica.config.json").write_text(json.dumps(document), encoding="utf-8")
    return root, document
