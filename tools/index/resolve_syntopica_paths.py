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
        ("mem", "path"),
        ("engines", "brain", "path"),
        ("engines", "clips", "path"),
        ("newsletter", "acceptedSenders"),
        ("newsletter", "rejectedSenders"),
        ("newsletter", "rejectedBookingSenders"),
        ("projects", "aliases"),
        ("projects", "roots"),
        ("sessions", "desktopRoots"),
        ("clips", "legacyArchive"),
    )
    result: dict[tuple[str, ...], tuple[Path, ...]] = {}
    for field in fields:
        value: object = document
        for key in field:
            value = cast(Mapping[str, object], value)[key]
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
            ("clips", "legacyArchive"),
        )
        if contained and any(not path.is_relative_to(root) for path in resolved):
            raise InvalidSyntopicaConfigError(f"{'.'.join(field)} escapes the data directory")
        result[field] = resolved
    return result
