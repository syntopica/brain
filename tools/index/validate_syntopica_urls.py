"""Prevent authenticated remote URLs from entering configuration state."""

from __future__ import annotations

import re
from typing import cast
from urllib.parse import urlsplit

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


def validate_syntopica_urls(value: object) -> None:
    """Reject URL credentials and signed queries without exposing their values."""
    if isinstance(value, dict):
        for child in cast(dict[str, object], value).values():
            validate_syntopica_urls(child)
    elif isinstance(value, list):
        for child in cast(list[object], value):
            validate_syntopica_urls(child)
    elif isinstance(value, str):
        if "://" in value:
            try:
                url = urlsplit(value)
                unsafe = (
                    url.password is not None
                    or (
                        url.username is not None
                        and not (url.scheme == "ssh" and url.username == "git")
                    )
                    or bool(url.query)
                    or bool(url.fragment)
                )
            except ValueError:
                raise InvalidSyntopicaConfigError(
                    "Configuration contains an invalid remote URL"
                ) from None
            if unsafe:
                raise InvalidSyntopicaConfigError(
                    "Remote URL must not contain credentials or query strings"
                )
        elif re.match(r"^[^/@\s]+@[^/\s:]+:", value) and not value.startswith("git@"):
            raise InvalidSyntopicaConfigError("Remote URL must not contain authentication material")
