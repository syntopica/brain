"""Configuration validation failures without credential-bearing values."""

from __future__ import annotations


class InvalidSyntopicaConfigError(Exception):
    """The selected configuration violates the data directory contract."""
