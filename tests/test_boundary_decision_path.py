"""An instance's boundary decision is a path it owns, inside its data directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from tests.syntopica_test_directory import syntopica_test_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config


def test_boundary_decision_is_an_instance_path(tmp_path: Path) -> None:
    """The acceptance of a model boundary is the operator's, so it lives in the
    instance: unset it is absent, set it must stay inside the data directory,
    and a declared file that is missing is a finding rather than a fallback."""
    root, document = syntopica_test_directory(tmp_path)
    config_file = root / "syntopica.config.json"
    assert root / "decision.json" not in load_syntopica_config(root, {}).configured_paths
    clips = cast(dict[str, object], document.setdefault("clips", {}))
    clips["boundaryDecision"] = "decision.json"
    config_file.write_text(json.dumps(document), encoding="utf-8")
    assert root / "decision.json" in load_syntopica_config(root, {}).configured_paths
    clips["boundaryDecision"] = "../outside.json"
    config_file.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(InvalidSyntopicaConfigError):
        load_syntopica_config(root, {})
