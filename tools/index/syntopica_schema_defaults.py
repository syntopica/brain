"""Read optional defaults directly from the shared wire schema."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import cast


def syntopica_schema_defaults(schema: Mapping[str, object]) -> dict[str, object]:
    """Collect annotated defaults without inventing required values."""
    result: dict[str, object] = {}
    for key, child in cast(dict[str, Mapping[str, object]], schema.get("properties", {})).items():
        if "default" in child:
            result[key] = deepcopy(child["default"])
        elif child.get("type") == "object":
            nested = syntopica_schema_defaults(child)
            if nested:
                result[key] = nested
    return result
