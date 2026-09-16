"""Where in a page a query's words appear, as a heading and a file line number."""

import re

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = "---"
_FENCES = 2  # a page's frontmatter opens and closes with one


def matching_section(text: str, terms: list[str]) -> tuple[str, int, str]:
    """Return the heading, 1-based line number and text of the best matching line.

    ``text`` is the whole file, frontmatter included, and the number counts from
    its first line: a citation the reader cannot open at the number given is
    worse than no citation. Counting a body that started after the frontmatter
    reported line 67 for a line that is at 86 on the live wiki (reproduced by
    review, 2026-09-16).

    Best means most distinct query terms on one line, earliest line breaking a
    tie. A heading is scored as well as remembered, because the question is
    often the heading, and a page ranked on its heading alone used to be printed
    with no line at all.

    Frontmatter is scored too -- `summary:` is frequently the line that answers
    -- but only wins when nothing in the body matched. It is what the page says
    about itself; a section is what it says.
    """
    heading = ""
    best = ("", 0, "")
    best_rank = (0, 0, 0)
    fences = 0
    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip() == _FENCE and fences < _FENCES:
            fences += 1
            continue
        in_frontmatter = fences == 1
        found = _HEADING.match(line)
        if found and not in_frontmatter:
            heading = found.group(0).strip()
        folded = line.lower()
        score = sum(1 for term in set(terms) if term in folded)
        # On equal score prefer prose to its own heading: the heading names the
        # section, which is already reported, while the line carries the answer.
        rank = (0 if in_frontmatter else 1, score, 0 if found else 1)
        if score and rank > best_rank:
            best_rank = rank
            best = ("" if in_frontmatter else heading, number, line.strip())
    return best
