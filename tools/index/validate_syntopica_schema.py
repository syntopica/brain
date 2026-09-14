"""Validate the finite JSON Schema vocabulary used by Syntopica."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import cast

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.syntopica_config_schema import SYNTOPICA_CONFIG_SCHEMA
from tools.index.syntopica_schema_type_matches import syntopica_schema_type_matches
from tools.index.validate_syntopica_uri import validate_syntopica_uri


def validate_syntopica_schema(
    value: object,
    schema: Mapping[str, object] = SYNTOPICA_CONFIG_SCHEMA,
    location: str = "configuration",
) -> None:
    """Validate against the wire schema without echoing input values.

    This implements only the keywords used in the bundled schema. Unknown
    assertion keywords fail closed instead of silently weakening validation.
    """
    supported = {
        "$schema",
        "title",
        "description",
        "type",
        "default",
        "properties",
        "additionalProperties",
        "required",
        "items",
        "enum",
        "minimum",
        "minLength",
        "pattern",
        "format",
        "x-path-kind",
    }
    if schema.keys() - supported:
        raise InvalidSyntopicaConfigError("Unsupported configuration schema keyword")
    kind = schema["type"]
    kinds = [kind] if isinstance(kind, str) else cast(list[str], kind)
    if not any(syntopica_schema_type_matches(value, name) for name in kinds):
        raise InvalidSyntopicaConfigError(f"{location}: invalid type")
    if "enum" in schema and value not in cast(list[object], schema["enum"]):
        raise InvalidSyntopicaConfigError(f"{location}: unregistered value")
    if isinstance(value, dict):
        fields = cast(dict[str, object], value)
        properties = cast(dict[str, Mapping[str, object]], schema["properties"])
        if schema.get("additionalProperties") is False and fields.keys() - properties.keys():
            raise InvalidSyntopicaConfigError(f"{location}: unknown key")
        if set(cast(list[str], schema.get("required", []))) - fields.keys():
            raise InvalidSyntopicaConfigError(f"{location}: missing required key")
        for key, child in fields.items():
            validate_syntopica_schema(child, properties[key], f"{location}.{key}")
    elif isinstance(value, list):
        for child in cast(list[object], value):
            validate_syntopica_schema(child, cast(Mapping[str, object], schema["items"]), location)
    elif isinstance(value, str):
        if schema.get("format") == "uri":
            validate_syntopica_uri(value)
        if len(value) < cast(int, schema.get("minLength", 0)):
            raise InvalidSyntopicaConfigError(f"{location}: empty string")
        if "pattern" in schema and re.search(cast(str, schema["pattern"]), value) is None:
            raise InvalidSyntopicaConfigError(f"{location}: invalid string format")
    elif isinstance(value, (int, float)) and "minimum" in schema:
        if value < cast(int, schema["minimum"]):
            raise InvalidSyntopicaConfigError(f"{location}: version must be positive")
