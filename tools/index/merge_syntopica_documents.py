"""Recursive configuration overlays preserve unspecified sibling fields."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import cast


def merge_syntopica_documents(
    base: Mapping[str, object], overlay: Mapping[str, object]
) -> dict[str, object]:
    """Copy and merge object members; replace arrays and explicit nulls."""
    result = deepcopy(dict(base))
    for key, value in overlay.items():
        previous = result.get(key)
        if isinstance(previous, dict) and isinstance(value, dict):
            result[key] = merge_syntopica_documents(
                cast(dict[str, object], previous), cast(dict[str, object], value)
            )
        else:
            result[key] = deepcopy(value)
    return result
