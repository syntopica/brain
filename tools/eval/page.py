"""The shape every retrieval baseline here reads a wiki page as."""

from pathlib import Path
from typing import TypedDict


class Page(TypedDict):
    """One wiki page reduced to what a retrieval baseline scores.

    Title and summary are separate fields rather than part of the body because
    they are what a reader sees first under SCHEMA's query discipline, and
    `keyword_scores` weights them above the prose for exactly that reason.
    `links` holds page ids, already narrowed to targets that resolve. `path` is
    the file this came from and `text` its whole content, frontmatter included:
    a reader sent to a line needs the line number the file has, not the one the
    body would have if it started at 1.

    Annotation-only, so the modules that use it import it under
    `TYPE_CHECKING` by its dotted path: mypy names these files by their
    location, while at runtime they import each other by bare name off the
    `sys.path` entry `run.py` adds.
    """

    id: str
    path: Path
    text: str
    title: str
    summary: str
    body: str
    links: set[str]
