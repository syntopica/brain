"""Whether a requested page id has the shape a page id can have."""

MAX_LENGTH = 512


def valid_page_id(page_id: str) -> bool:
    """`<directory>/<stem>`, where the stem is one plain path segment.

    The directory part is checked later against the configured page roots, by
    exact match, so it may only name a root the instance itself declared; the
    stem is the part a caller controls, and is refused anything that could
    leave that root: a separator, a parent or current segment, a leading dot,
    a NUL. An absolute id is refused outright.
    """
    if not page_id or len(page_id) > MAX_LENGTH or page_id.startswith("/"):
        return False
    if "\\" in page_id or "\0" in page_id:
        return False
    directory, _, stem = page_id.rpartition("/")
    return bool(directory) and bool(stem) and not stem.startswith(".")
