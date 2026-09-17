"""Report pages that break the conventions SCHEMA.md documents."""

import os
import re
from pathlib import Path

from tools.graph.parse_frontmatter import parse_frontmatter
from tools.index.summary_of import summary_of

FENCE = len("---")
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ("title", "type", "updated")


def page_convention_issues(root: Path, directories: tuple[Path, ...]) -> list[str]:
    """Name every page whose filename or frontmatter the schema rejects.

    Lint used to check only the index and its links, while the README, the
    schema and the packaged skill all promised filenames, frontmatter and
    summaries were checked; a stranger reading `0 issues` read it as the whole
    schema having passed.
    """
    issues = []
    for directory in directories:
        for path in sorted(directory.glob("*.md")):
            page = Path(os.path.relpath(path, root)).with_suffix("").as_posix()
            if not KEBAB_CASE.match(path.stem):
                issues.append(f"filename: {page} is not kebab-case")
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---") or text.find("\n---", FENCE) == -1:
                issues.append(f"frontmatter: {page} has no closed frontmatter block")
                continue
            fields = parse_frontmatter(text)
            missing = [field for field in REQUIRED_FIELDS if not fields.get(field)]
            if not summary_of(path):
                missing.append("summary")
            if missing:
                # A folded YAML scalar reads as absent here, and that is the
                # finding: the schema requires each of these on one line.
                issues.append(
                    f"frontmatter: {page} has no single-line {', '.join(sorted(missing))}"
                )
    return issues
