"""The page type implied by a page directory, for pages without a `type:`."""

DIRECTORY_TYPES = {
    "projects": "project",
    "business": "business",
    "people": "person",
    "topics": "topic",
    "personal": "personal",
}


def directory_type(directory: str) -> str:
    """The singular type of a known page directory, else the directory name."""
    return DIRECTORY_TYPES.get(directory, directory)
