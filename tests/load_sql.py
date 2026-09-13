"""Load SQL fixtures relative to the test suite."""

from pathlib import Path


def load_sql(name: str) -> str:
    """Read a named SQL fixture without changing its statement text."""
    return (Path(__file__).resolve().parent / "sql" / f"{name}.sql").read_text(encoding="utf-8")
