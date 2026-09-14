"""Classify resolved paths using the presence policy declared in the schema."""

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.syntopica_config_schema import SYNTOPICA_CONFIG_SCHEMA


def classify_syntopica_paths(
    paths: Mapping[tuple[str, ...], tuple[Path, ...]],
) -> dict[str, tuple[Path, ...]]:
    """Require every resolved field to explicitly declare required or state."""
    groups: dict[str, list[Path]] = {"required": [], "state": []}
    for field, values in paths.items():
        node: Mapping[str, object] = SYNTOPICA_CONFIG_SCHEMA
        for key in field:
            node = cast(Mapping[str, Mapping[str, object]], node["properties"])[key]
        kind = node.get("x-path-kind")
        if not isinstance(kind, str) or kind not in groups:
            raise InvalidSyntopicaConfigError(
                f"{'.'.join(field)} must declare x-path-kind as required or state"
            )
        groups[kind].extend(values)
    return {kind: tuple(values) for kind, values in groups.items()}
