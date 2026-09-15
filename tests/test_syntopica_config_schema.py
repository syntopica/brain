"""The public configuration schema and its supported validation vocabulary."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import cast

import pytest

from tests.tool_paths import ROOT
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.syntopica_config_schema import SYNTOPICA_CONFIG_SCHEMA
from tools.index.validate_syntopica_schema import validate_syntopica_schema


def example_document() -> dict[str, object]:
    """Read the committed example rather than a document that stays private.

    It lived in the split design spec until 2026-09-13, which made the public
    suite depend on the migration's own record. The example is documentation
    the engine ships anyway, so it is a file beside the schema it illustrates.
    """
    example = ROOT / "schema/syntopica.config.example.json"
    return cast(dict[str, object], json.loads(example.read_text(encoding="utf-8")))


def test_schema_is_a_closed_object() -> None:
    assert SYNTOPICA_CONFIG_SCHEMA["additionalProperties"] is False


def test_schema_requires_version_and_instance() -> None:
    assert set(cast(list[str], SYNTOPICA_CONFIG_SCHEMA["required"])) == {
        "schemaVersion",
        "instanceId",
        "brain",
        "engines",
    }


def test_schema_file_and_module_agree() -> None:
    on_disk = json.loads((ROOT / "schema/syntopica-config.schema.json").read_text(encoding="utf-8"))
    assert on_disk == SYNTOPICA_CONFIG_SCHEMA
    assert on_disk["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_schema_accepts_the_shipped_example() -> None:
    validate_syntopica_schema(example_document())


@pytest.mark.parametrize(
    "section",
    [
        None,
        "brain",
        "engines",
        "capture",
        "runners",
        "browser",
        "newsletter",
        "projects",
        "clips",
        "atrium",
        "conversations",
    ],
)
def test_schema_rejects_unknown_key(section: str | None) -> None:
    document = example_document()
    target = document if section is None else cast(dict[str, object], document[section])
    target["unknown"] = True
    with pytest.raises(InvalidSyntopicaConfigError):
        validate_syntopica_schema(document)


@pytest.mark.parametrize(
    "path", ["/absolute", "..", "../outside", "a/../b", "a/..", "a//../b", "safe\n/../../outside"]
)
@pytest.mark.parametrize(
    "section,key",
    [
        ("brain", "sources"),
        ("brain", "index"),
        ("brain", "ledger"),
        ("clips", "archive"),
        ("atrium", "path"),
        ("conversations", "path"),
        ("newsletter", "acceptedSenders"),
        ("newsletter", "rejectedSenders"),
        ("newsletter", "rejectedBookingSenders"),
        ("projects", "aliases"),
    ],
)
def test_content_paths_are_relative(section: str, key: str, path: str) -> None:
    document = example_document()
    cast(dict[str, object], document[section])[key] = path
    with pytest.raises(InvalidSyntopicaConfigError):
        validate_syntopica_schema(document)


@pytest.mark.parametrize(
    "origin",
    [
        "https://user:secret@example.test",
        "https://user@example.test",
        "https://example.test/path",
        "https://example.test?token=secret",
        "https://example.test#fragment",
        "ftp://example.test",
        "https://",
        "https://example.test\n",
        "https://example.test:bad",
        "https://example.test\\evil",
        "https://[:::]",
        "https://example.test:65536",
    ],
)
def test_origin_rejects_non_origins(origin: str) -> None:
    document = example_document()
    cast(dict[str, object], document["capture"])["origin"] = origin
    with pytest.raises(InvalidSyntopicaConfigError):
        validate_syntopica_schema(document)


@pytest.mark.parametrize(
    "origin", [None, "https://example.test", "http://localhost:8080/", "https://[::1]:443"]
)
def test_origin_accepts_origins(origin: str | None) -> None:
    document = example_document()
    cast(dict[str, object], document["capture"])["origin"] = origin
    validate_syntopica_schema(document)


@pytest.mark.parametrize("value", [0, -1, True, "1", 1.5, None])
def test_versions_must_be_positive_integers(value: object) -> None:
    for section in (None, "brain", "clips"):
        document = deepcopy(example_document())
        if section is None:
            document["schemaVersion"] = value
        else:
            engines = cast(dict[str, dict[str, object]], document["engines"])
            engines[section]["apiVersion"] = value
        with pytest.raises(InvalidSyntopicaConfigError):
            validate_syntopica_schema(document)


@pytest.mark.parametrize("runner", [None, "codex", "agy-fine", "agy-bulk", "cursor", "manual"])
def test_registered_runners(runner: str | None) -> None:
    document = example_document()
    document["runners"] = dict.fromkeys(("synthesis", "grade", "triage", "triageRefiner"), runner)
    validate_syntopica_schema(document)


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("brain", "pages", ["../escape"]),
        ("capture", "mirror", "on"),
        ("runners", "grade", "shell"),
        ("browser", "executable", 1),
        ("projects", "roots", [1]),
        ("engines", "brain", {"path": "x", "apiVersion": 1, "unknown": 1}),
    ],
)
def test_invalid_field_types(section: str, key: str, value: object) -> None:
    document = example_document()
    cast(dict[str, object], document[section])[key] = value
    with pytest.raises(InvalidSyntopicaConfigError):
        validate_syntopica_schema(document)
