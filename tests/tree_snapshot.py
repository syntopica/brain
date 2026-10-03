"""Every file under a directory with its bytes, to prove a command wrote nothing."""

from pathlib import Path


def tree_snapshot(root: Path) -> dict[str, bytes]:
    """Relative path to content for every regular file, symlinks named by target."""
    snapshot: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[relative] = str(path.readlink()).encode()
        elif path.is_file():
            snapshot[relative] = path.read_bytes()
    return snapshot
