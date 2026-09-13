"""Reject ambiguous duplicate JSON object members."""

from __future__ import annotations

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


def syntopica_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a parsed object only when each key is unique."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidSyntopicaConfigError("Configuration contains a duplicate key")
        result[key] = value
    return result
