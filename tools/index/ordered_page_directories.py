"""Keep established wiki ordering while accepting arbitrary configured folders."""

from pathlib import Path


def ordered_page_directories(directories: tuple[Path, ...]) -> tuple[Path, ...]:
    """Order known sections as before, followed by other sections in config order."""
    names = ("projects", "business", "people", "topics", "personal")
    ordered = [directory for name in names for directory in directories if directory.name == name]
    ordered.extend(directory for directory in directories if directory.name not in names)
    return tuple(ordered)
