"""The shape every retrieval baseline here reads a wiki page as."""

from typing import TypedDict


class Page(TypedDict):
    """One wiki page reduced to what a retrieval baseline scores.

    Title and summary are separate fields rather than part of the body because
    they are what a reader sees first under SCHEMA's query discipline, and
    `keyword_scores` weights them above the prose for exactly that reason.
    `links` holds page ids, already narrowed to targets that resolve.

    Annotation-only, so the modules that use it import it under
    `TYPE_CHECKING` by its dotted path: mypy names these files by their
    location, while at runtime they import each other by bare name off the
    `sys.path` entry `run.py` adds.
    """

    id: str
    title: str
    summary: str
    body: str
    links: set[str]
