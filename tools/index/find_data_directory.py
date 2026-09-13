"""Resolve a caller's data directory without crossing its Git boundary."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from tools.index.data_directory_not_found_error import DataDirectoryNotFoundError


def find_data_directory(explicit: str | None, environ: Mapping[str, str], start: Path) -> Path:
    """Select an explicit directory, an environment path or a bounded ancestor."""
    start = start.resolve()
    selected = explicit if explicit is not None else environ.get("SYNTOPICA_DATA")
    if selected is not None:
        candidate = (start / selected).resolve()
        if (candidate / "syntopica.config.json").is_file():
            return candidate
        raise DataDirectoryNotFoundError(
            f"No syntopica.config.json in selected directory {candidate}; started at {start}"
        )
    for candidate in (start, *start.parents):
        if (candidate / "syntopica.config.json").is_file():
            return candidate
        if (candidate / ".git").exists():
            break
    raise DataDirectoryNotFoundError(f"No syntopica.config.json found walking upward from {start}")
