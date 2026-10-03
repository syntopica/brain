"""Configuration health as a machine-readable document of fixed codes."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.index.doctor_checks import doctor_checks

SCHEMA_VERSION = 1


def doctor_document(
    root: Path, environ: Mapping[str, str], skip: frozenset[str] = frozenset()
) -> dict[str, Any]:
    """Every check as `name`, `ok` and `code`; the messages are left out.

    A message can name a configured path or an executable; a code cannot, so a
    reader may store and display this document without carrying instance data.
    A skipped check still appears, passing with code `skipped`.
    """
    checks = tuple(
        (True, message, "skipped") if message.partition(":")[0] in skip else (passed, message, code)
        for passed, message, code in doctor_checks(root, environ)
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "ok": all(passed for passed, _, _ in checks),
        "checks": [
            {"name": message.partition(":")[0], "ok": passed, "code": code}
            for passed, message, code in checks
        ],
    }
