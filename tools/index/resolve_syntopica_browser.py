"""Resolve executable paths while preserving commands found through PATH."""

from __future__ import annotations

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


def resolve_syntopica_browser(executable: str | None, directory: Path) -> str | None:
    """Resolve explicit paths against their origin; retain bare command names."""
    if executable is None or "/" not in executable:
        return executable
    try:
        return str((directory / executable).resolve())
    except (OSError, RuntimeError, ValueError):
        raise InvalidSyntopicaConfigError("Browser executable path cannot be resolved") from None
