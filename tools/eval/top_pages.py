"""The pages a baseline would have a reader open."""


def top_pages(scores: dict[str, float], k: int) -> list[str]:
    """Highest score first, page id breaking a tie so a run is reproducible.

    A page scoring zero is never returned, however few pages are above it. The
    alternative pads the answer to k with whatever sorted first, and a padded
    answer is what makes an eval report recall on questions the baseline
    actually failed.
    """
    ranked = sorted(
        (page_id for page_id, score in scores.items() if score > 0),
        key=lambda page_id: (-scores[page_id], page_id),
    )
    return ranked[:k]
