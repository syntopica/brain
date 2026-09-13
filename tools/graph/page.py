"""The shape of a wiki page as the graph tooling passes it around."""

from typing import TypedDict


class Page(TypedDict):
    """One page, as `build.py` reads it off disk and the scorers consume it.

    `id` is the `<dir>/<stem>` the wiki links by, `sources` the frontmatter
    `sources:` block, and `targets` every `[[dir/page]]` the body names, in
    order and with repeats - deduplication is the caller's decision, because
    counting an edge twice and scoring it twice are different questions.
    """

    id: str
    dir: str
    title: str
    type: str
    updated: str
    sources: set[str]
    targets: list[str]
