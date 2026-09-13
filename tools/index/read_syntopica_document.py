"""Read a configuration document without leaking JSON or filesystem errors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.reject_syntopica_json_constant import reject_syntopica_json_constant
from tools.index.syntopica_json_object import syntopica_json_object
from tools.index.validate_syntopica_urls import validate_syntopica_urls


def read_syntopica_document(path: Path) -> dict[str, object]:
    """Read a JSON object and reject duplicate keys and credential-bearing URLs."""
    try:
        value: object = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=syntopica_json_object,
            parse_constant=reject_syntopica_json_constant,
        )
    except (OSError, ValueError, UnicodeError):
        raise InvalidSyntopicaConfigError("Cannot read configuration as UTF-8 JSON") from None
    if not isinstance(value, dict):
        raise InvalidSyntopicaConfigError("Configuration must be a JSON object")
    validate_syntopica_urls(value)
    return cast(dict[str, object], value)
