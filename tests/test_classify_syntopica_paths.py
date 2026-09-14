"""Resolved paths cannot silently acquire an implicit presence policy."""

from pathlib import Path
from typing import cast

import pytest

from tools.index.classify_syntopica_paths import classify_syntopica_paths
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.syntopica_config_schema import SYNTOPICA_CONFIG_SCHEMA


@pytest.mark.parametrize("kind", [None, "optional", False])
def test_path_classification_must_be_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: object
) -> None:
    properties = cast(dict[str, dict[str, object]], SYNTOPICA_CONFIG_SCHEMA["properties"])
    brain = cast(dict[str, dict[str, object]], properties["brain"]["properties"])
    path_schema = brain["pages"]
    monkeypatch.delitem(path_schema, "x-path-kind")
    if kind is not None:
        monkeypatch.setitem(path_schema, "x-path-kind", kind)
    with pytest.raises(InvalidSyntopicaConfigError, match=r"brain\.pages must declare x-path-kind"):
        classify_syntopica_paths({("brain", "pages"): (tmp_path / "notes",)})


def test_new_state_path_uses_its_schema_classification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    properties = cast(dict[str, dict[str, object]], SYNTOPICA_CONFIG_SCHEMA["properties"])
    monkeypatch.setitem(properties, "newState", {"type": "string", "x-path-kind": "state"})
    state = tmp_path / "new-state"
    assert classify_syntopica_paths({("newState",): (state,)}) == {
        "required": (),
        "state": (state,),
    }
