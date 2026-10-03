"""Resolve a page id to its file, only inside a configured page root."""

import os
from pathlib import Path

from tools.index.valid_page_id import valid_page_id


def page_path(page_id: str, root: Path, directories: tuple[Path, ...]) -> Path | None:
    """The page's file, or None when the id names nothing inside a page root.

    The directory part must equal a configured root's id exactly, the same
    `<relative dir>` the scan keys pages by, so `notes/../notes/x` or
    `../elsewhere/x` match nothing unless the configuration itself declares
    that root. A symlinked page whose target resolves outside its root is
    refused: following it would read a file the roots never named.
    """
    if not valid_page_id(page_id):
        return None
    directory_id, _, stem = page_id.rpartition("/")
    for directory in directories:
        if Path(os.path.relpath(directory, root)).as_posix() != directory_id:
            continue
        path = directory / f"{stem}.md"
        if not path.is_file() or not path.resolve().is_relative_to(directory.resolve()):
            return None
        return path
    return None
