"""Summary of: extracted from build.py."""

from pathlib import Path

from tools.index.raw_summary import raw_summary


def summary_of(path: Path) -> str:
    """The page's `summary:` with its YAML quoting removed, or "" if it has none.

    A page with no frontmatter, or whose frontmatter is never closed, has no
    summary rather than being an error: the index still lists it, and the
    caller reports it on stderr.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    value = raw_summary(text[3:end])
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value
