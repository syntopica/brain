"""Validate the URI format used for capture origins."""

from __future__ import annotations

from urllib.parse import urlsplit

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


def validate_syntopica_uri(value: str) -> None:
    """Check host literals and port ranges beyond the schema's origin pattern."""
    try:
        parsed = urlsplit(value)
        if parsed.hostname is None or (parsed.port is not None and parsed.port < 0):
            raise ValueError
    except ValueError:
        raise InvalidSyntopicaConfigError("Configuration contains an invalid origin") from None
