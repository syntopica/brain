"""Configuration health as a machine-readable document of fixed codes."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.index.doctor_checks import doctor_checks

SCHEMA_VERSION = 1


def doctor_document(root: Path, environ: Mapping[str, str]) -> dict[str, Any]:
    """Every check as `name`, `ok` and `code`; the messages are left out.

    A message can name a configured path or an executable; a code cannot, so a
    reader may store and display this document without carrying instance data.
    """
    checks = doctor_checks(root, environ)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "ok": all(passed for passed, _, _ in checks),
        "checks": [
            {"name": message.partition(":")[0], "ok": passed, "code": code}
            for passed, message, code in checks
        ],
    }
