"""Scan pages: extracted from build.py."""

import os
import re
from pathlib import Path

from tools.graph.frontmatter_sources import frontmatter_sources
from tools.graph.page import Page
from tools.graph.parse_frontmatter import parse_frontmatter

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
            targets = []
            for raw in LINK.findall(body):
                t = raw.strip()
                if "/" not in t:
                    continue  # [[SCHEMA]] / [[index]] style root refs are not pages
                targets.append(t)
            pages[pid] = {
                "id": pid,
                "dir": d,
                "title": fm.get("title", f.stem),
                "type": fm.get("type", d.rstrip("s")),
                "updated": fm.get("updated", ""),
                "sources": frontmatter_sources(text),
                "targets": targets,
            }
    return pages
