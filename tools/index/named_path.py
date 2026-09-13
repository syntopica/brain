"""Name a configured path the shortest way that still identifies it."""

from pathlib import Path


def named_path(path: Path, root: Path) -> str:
    """Show the path relative to the instance, or whole when it lies outside it.

    Not every configured path is inside the data directory: a desktop session
    store sits under the user's Library, and `relative_to` raises on it.
    """
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
