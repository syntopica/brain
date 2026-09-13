"""Track which configuration file supplied each effective value."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast


def syntopica_value_origins(
    document: Mapping[str, object], directory: Path, prefix: tuple[str, ...] = ()
) -> dict[tuple[str, ...], Path]:
    """Record leaf origins, treating an array as one replacement value."""
    result: dict[tuple[str, ...], Path] = {}
    for key, value in document.items():
        field = (*prefix, key)
        if isinstance(value, dict):
            result.update(syntopica_value_origins(cast(dict[str, object], value), directory, field))
        else:
            result[field] = directory
    return result
