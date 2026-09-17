"""Scan pages: extracted from build.py."""

import os
import re
from pathlib import Path

from tools.graph.frontmatter_sources import frontmatter_sources
from tools.graph.page import Page
from tools.graph.parse_frontmatter import parse_frontmatter
from tools.graph.resolve_bare_target import resolve_bare_target

LINK = re.compile(r"\[\[([^\]|#]+)")

FENCE = len("---")


def scan_pages(root: Path, directories: tuple[Path, ...]) -> dict[str, Page]:
    """Every page under the configured page directories, keyed by `<dir>/<stem>`.

    index.md and SCHEMA.md are deliberately absent: index links everything, so
    including it would flatten the orphan signal lint relies on.
    """
    pages: dict[str, Page] = {}
    for directory in directories:
        d = Path(os.path.relpath(directory, root)).as_posix()
        for f in sorted(directory.glob("*.md")):
            pid = f"{d}/{f.stem}"
            text = f.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            body = (
                text[text.find("\n---", FENCE) + len("\n---") :] if text.startswith("---") else text
            )
            body = re.sub(r"`[^`]*`", "", body)  # code spans quote link syntax, they are not links
            targets = [raw.strip() for raw in LINK.findall(body)]
            pages[pid] = {
                "id": pid,
                "dir": d,
                "title": fm.get("title", f.stem),
                "type": fm.get("type", d.rstrip("s")),
                "updated": fm.get("updated", ""),
                "sources": frontmatter_sources(text),
                "targets": targets,
            }
    # Resolution needs every page, so it happens once the scan is complete.
    by_basename: dict[str, tuple[str, ...]] = {}
    for page in pages:
        stem = page.rpartition("/")[2]
        by_basename[stem] = (*by_basename.get(stem, ()), page)
    for page in pages.values():
        resolved = []
        for target in page["targets"]:
            if "/" in target:
                resolved.append(target)
                continue
            bare = resolve_bare_target(target, by_basename)
            if bare is not None:
                resolved.append(bare)
        page["targets"] = resolved
    return pages
