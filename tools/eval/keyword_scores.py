"""How well each page's own words match a question."""

from math import log
from typing import TYPE_CHECKING

from page_text import page_text
from query_terms import query_terms

if TYPE_CHECKING:
    from tools.eval.page import Page

# What a reader sees before deciding to open a page, weighted as such.
TITLE_WEIGHT = 6.0
SUMMARY_WEIGHT = 3.0
BODY_WEIGHT = 1.0
# One mention proves the subject appears; the tenth proves nothing more.
BODY_SATURATION = 3.0


def keyword_scores(question: str, pages: dict[str, "Page"]) -> dict[str, float]:
    """Score every page in `pages` for how well its own words match `question`.

    Inverse-page-frequency weighting, with title and summary counted above
    the body, because SCHEMA's query discipline says a reader reads those first
    and this baseline exists to score that discipline rather than a generic
    search engine.

    Body counts saturate. Without it a page that mentions Cloudflare forty times
    outranks the page about Cloudflare, and the long hub pages here would win
    every question by length alone.

    A term no page carries contributes nothing rather than raising an error: a
    question this wiki cannot answer is a question worth asking of it, and
    `expected_refusal` is the whole reason the eval set will carry some.
    """
    terms = query_terms(question)
    corpus = {
        term: sum(1 for page in pages.values() if term in page_text(page)) for term in set(terms)
    }
    scores: dict[str, float] = {}
    for page_id, page in pages.items():
        total = 0.0
        for term in terms:
            carrying = corpus[term]
            if carrying == 0:
                continue
            rarity = log(len(pages) / carrying) + 1.0
            body_hits = min(page["body"].lower().count(term), BODY_SATURATION)
            total += rarity * (
                TITLE_WEIGHT * (term in page["title"].lower())
                + SUMMARY_WEIGHT * (term in page["summary"].lower())
                + BODY_WEIGHT * body_hits
            )
        scores[page_id] = total
    return scores
