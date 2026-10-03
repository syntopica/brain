"""Report configuration health with only credential-free status messages."""

from collections.abc import Mapping
from pathlib import Path

from tools.index.doctor_checks import doctor_checks


def doctor_report(root: Path, environ: Mapping[str, str]) -> int:
    """Print one line per available check and return a shell-compatible status."""
    checks = doctor_checks(root, environ)
    for passed, message, _ in checks:
        print(f"{'PASS' if passed else 'FAIL'} {message}")
    return int(any(not passed for passed, _, _ in checks))
