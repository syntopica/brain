"""Resolve a link written without its directory, when that is unambiguous."""

from collections.abc import Mapping


def resolve_bare_target(target: str, by_basename: Mapping[str, tuple[str, ...]]) -> str | None:
    """The page id a `[[name]]` link means, or None when nothing is meant.

    The documented form carries the directory, and the scanner used to drop
    every target without one - silently, so six links in a three-page wiki
    produced a graph with no edges and three orphans, and lint reported no
    issue. A name that matches exactly one page is not ambiguous, so it now
    resolves.

    Two other cases stay unresolved on purpose. A name matching several pages
    is genuinely ambiguous and returns the name itself, which the caller reports
    as unresolved. A name matching no page at all is ignored, because citation
    markers like `[[S1]]` are written in this position in numbers - 8,593 of
    them in one live wiki - and are not page links.
    """
    matches = by_basename.get(target, ())
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return target
    return None
