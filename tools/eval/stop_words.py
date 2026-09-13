"""Words a question carries that say nothing about which page answers it.

Short on purpose. A long stop list is a second, unmeasured retrieval decision
hiding inside the baseline - drop "server" as too common and the baseline stops
finding the page about servers. These are function words only: nothing here
names a thing this wiki holds.
"""

from typing import Final

STOP_WORDS: Final[frozenset[str]] = frozenset(
    [
        "a",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "has",
        "have",
        "how",
        "i",
        "in",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "their",
        "there",
        "these",
        "this",
        "to",
        "under",
        "use",
        "used",
        "using",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
        "you",
        "your",
    ]
)
