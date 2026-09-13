"""Resolve the calling tool's instance through the shared configuration contract."""

import os
from pathlib import Path

from tools.index.find_data_directory import find_data_directory
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.syntopica_config import SyntopicaConfig


def current_syntopica_config(explicit: str | None = None) -> SyntopicaConfig:
    """Load the explicit or discovered data directory without import-time state."""
    root = find_data_directory(explicit, os.environ, Path.cwd())
    return load_syntopica_config(root, os.environ)
