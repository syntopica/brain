"""Non-finite Python JSON extensions are not configuration values."""

from __future__ import annotations

from typing import Never

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


def reject_syntopica_json_constant(value: str) -> Never:
    """Refuse NaN and infinity without echoing source content."""
    raise InvalidSyntopicaConfigError("Configuration contains a non-JSON numeric constant")
