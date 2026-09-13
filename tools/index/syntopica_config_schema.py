"""The parsed wire schema for a data directory's configuration."""

from __future__ import annotations

import json
from pathlib import Path

SYNTOPICA_CONFIG_SCHEMA: dict[str, object] = json.loads(
    (Path(__file__).resolve().parents[2] / "schema" / "syntopica-config.schema.json").read_text(
        encoding="utf-8"
    )
)
