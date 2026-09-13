"""What share of the pages that should answer a question were retrieved."""


def recall_at_k(retrieved: list[str], expected: list[str]) -> float:
    """Return the share of `expected` page ids present in `retrieved`.

    Recall, not precision, and k is fixed by the caller at the five pages
    SCHEMA's query discipline allows. Precision at a budget of five says little
    here: several pages are a legitimate answer to most questions in this wiki,
    and a reader who opens two useful pages and three others has not failed.

    A question with no expected pages - the refusal cases - scores 1.0 when
    nothing was retrieved and 0.0 otherwise. That is the only place this metric
    rewards silence, and it is the property `expected_refusal` was named for.
    """
    if not expected:
        return 1.0 if not retrieved else 0.0
    found = sum(1 for page_id in expected if page_id in retrieved)
    return found / len(expected)
