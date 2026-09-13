"""Raised when no data directory could be identified."""

from __future__ import annotations


class DataDirectoryNotFoundError(Exception):
    """No syntopica.config.json was found by the selected resolution step."""
