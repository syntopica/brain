"""Render the fixture instance's index with the engine when it is reachable."""

from pathlib import Path


def rendered_fixture_index(brain: Path, directories: list[str]) -> str:
    """Use the real generator, or a plain map where the engine is not present.

    The same fixture builds instances for both engines, and only one of the two
    repositories ships the index generator. Falling back keeps the fixture
    honest about what it is: an instance shaped correctly, not a claim that the
    index matches what the generator would write. The tests that assert on
    generated output live beside the generator, where the import resolves.
    """
    try:
        from tools.index.ordered_page_directories import ordered_page_directories
        from tools.index.rendered import rendered
    except ImportError:
        lines = ["# Index", ""]
        for directory in directories:
            lines += [f"## {directory}", ""]
        return "\n".join(lines) + "\n"
    return rendered(brain, ordered_page_directories(tuple(brain / d for d in directories)))
