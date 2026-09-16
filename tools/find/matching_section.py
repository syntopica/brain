"""Where on a page a query's words actually appear, as a heading and a line."""

import re

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def matching_section(body: str, terms: list[str]) -> tuple[str, int, str]:
    """Return the heading, 1-based line number and text of the best matching line.

    A page here is up to 30 KB, and a hub is a stack of `## finding` sections.
    Returning the page alone sends the reader through all of it to find the one
    section that answered; returning the line and the heading above it makes the
    next read a bounded one. The whole point of the command is that a session
    stops paging through files it did not need.

    Best means most distinct query terms on one line, earliest line breaking a
    tie: a line carrying two of the words is about the question in a way a line
    carrying one is usually not. Frontmatter is included, because `summary:` is
    frequently the line that answers.
    """
    heading = ""
    best = ("", 0, "")
    best_score = 0
    for number, line in enumerate(body.splitlines(), start=1):
        found = _HEADING.match(line)
        if found:
            heading = found.group(0).strip()
            continue
        folded = line.lower()
        score = sum(1 for term in set(terms) if term in folded)
        if score > best_score:
            best_score = score
            best = (heading, number, line.strip())
    return best
