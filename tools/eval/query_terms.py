"""A question reduced to the words a search would use."""

import re

from stop_words import STOP_WORDS

WORD = re.compile(r"[a-z0-9][a-z0-9._-]*")


def query_terms(question: str) -> list[str]:
    """Lowercased word tokens, function words dropped, duplicates kept.

    Dots and hyphens survive inside a token because half the things this wiki
    is asked about are spelled that way - `example.pe`, `capture-archive`,
    `modelo 303`. Splitting on them would turn one distinctive term into two
    common ones, which is the failure a stemmer usually introduces and this
    baseline has no need to introduce.
    """
    return [
        word for word in WORD.findall(question.lower()) if word not in STOP_WORDS and len(word) > 1
    ]
