"""Resolve configuration paths using their defining files, with containment."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


def resolve_syntopica_paths(
    document: Mapping[str, object], origins: Mapping[tuple[str, ...], Path], root: Path
) -> dict[tuple[str, ...], tuple[Path, ...]]:
    """Resolve all content and checkout paths, including symlink targets."""
    fields = (
        ("brain", "pages"),
        ("brain", "sources"),
        ("brain", "index"),
        ("brain", "ledger"),
        ("clips", "archive"),
        ("atrium", "path"),
        ("conversations", "path"),
        ("engines", "brain", "path"),
        ("engines", "clips", "path"),
        ("engines", "atrium", "path"),
        ("engines", "agents", "path"),
        ("newsletter", "acceptedSenders"),
        ("newsletter", "rejectedSenders"),
        ("newsletter", "rejectedBookingSenders"),
        ("projects", "aliases"),
        ("projects", "roots"),
        ("sessions", "desktopRoots"),
        ("clips", "inbox"),
        ("clips", "boundaryDecision"),
    )
    # An instance declares the engines it uses; brain is the only one the
    # schema requires, so the others may be absent rather than null.
    optional = {
        ("engines", "clips", "path"),
        ("engines", "atrium", "path"),
        ("engines", "agents", "path"),
    }
    result: dict[tuple[str, ...], tuple[Path, ...]] = {}
    for field in fields:
        value: object = document
        for key in field:
            mapping = cast(Mapping[str, object], value)
            if key not in mapping and field in optional:
                value = None
                break
            value = mapping[key]
        if value is None:
            result[field] = ()
            continue
        values = cast(list[str], value) if isinstance(value, list) else [cast(str, value)]
        try:
            resolved = tuple((origins[field] / item).resolve() for item in values)
        except (OSError, RuntimeError, ValueError):
            raise InvalidSyntopicaConfigError("Configuration path cannot be resolved") from None
        contained = field[0] != "engines" and field not in (
            ("projects", "roots"),
            ("sessions", "desktopRoots"),
            ("clips", "inbox"),
        )
        if contained and any(not path.is_relative_to(root) for path in resolved):
            raise InvalidSyntopicaConfigError(f"{'.'.join(field)} escapes the data directory")
        result[field] = resolved
    return result
