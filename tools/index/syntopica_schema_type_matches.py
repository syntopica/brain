"""JSON types used by the configuration schema."""

from __future__ import annotations


def syntopica_schema_type_matches(value: object, kind: str) -> bool:
    """Match JSON types, keeping booleans distinct from integers."""
    match kind:
        case "object":
            return isinstance(value, dict)
        case "array":
            return isinstance(value, list)
        case "string":
            return isinstance(value, str)
        case "integer":
            return type(value) is int or (type(value) is float and value.is_integer())
        case "boolean":
            return isinstance(value, bool)
        case "null":
            return value is None
        case _:
            raise ValueError("Unsupported configuration schema type")
