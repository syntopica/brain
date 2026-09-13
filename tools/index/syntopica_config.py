"""The immutable, resolved configuration consumed by the engines."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyntopicaConfig:
    """Validated instance settings; every path is absolute and resolved."""

    data_root: Path
    schema_version: int
    instance_id: str
    pages: tuple[Path, ...]
    sources: Path
    index: Path
    ledger: Path
    archive: Path
    brain_path: Path
    clips_path: Path
    capture_origin: str | None
    capture_mirror: bool
    runners: Mapping[str, str | None]
    browser: str | None
    brain_api_version: int = 1
    clips_api_version: int = 1
    configured_paths: tuple[Path, ...] = ()
    legacy_archive: Path | None = None
    repository_url: str | None = None
    screening_scope: str = ""
    desktop_roots: tuple[Path, ...] = ()
