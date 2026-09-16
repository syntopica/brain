#!/usr/bin/env python3
"""Find the pages that answer a question, and the line on each that does.

    brain find "acme api key"

Model-free and offline: the same keyword baseline `tools/eval` measures, over
the configured page directories only. It exists because the alternative a
session reaches for is `grep -r`, which walks the captured sources beside the
pages -- on the wiki this was written for, 13,302 files and 9.7 GB, measured at
101s against 0.23s for the pages alone.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

from tools.eval.keyword_scores import keyword_scores
from tools.eval.load_pages import load_pages
from tools.eval.query_terms import query_terms
from tools.eval.top_pages import top_pages
from tools.find.matching_section import matching_section
from tools.index.data_directory_not_found_error import DataDirectoryNotFoundError
from tools.index.find_data_directory import find_data_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.ordered_page_directories import ordered_page_directories

_DEFAULT_LIMIT = 5


def main(argv: list[str] | None = None) -> int:
    """Print the ranked pages with the heading and line that matched."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+")
    parser.add_argument("--data", metavar="PATH")
    parser.add_argument("--limit", type=int, default=_DEFAULT_LIMIT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = find_data_directory(args.data, os.environ, Path.cwd())
        config = load_syntopica_config(root, os.environ)
    except (DataDirectoryNotFoundError, InvalidSyntopicaConfigError) as error:
        print(str(error), file=sys.stderr)
        return 1
    base = config.index.parent
    directories = tuple(directory.name for directory in ordered_page_directories(config.pages))
    question = " ".join(args.query)
    pages = load_pages(base, directories)
    terms = query_terms(question)
    hits: list[dict[str, str | int]] = []
    for page_id in top_pages(keyword_scores(question, pages), args.limit):
        heading, line, text = matching_section(pages[page_id]["body"], terms)
        hits.append(
            {
                "page": f"{os.path.relpath(base, Path.cwd())}/{page_id}.md",
                "title": pages[page_id]["title"],
                "heading": heading,
                "line": line,
                "text": text,
            }
        )
    if args.json:
        print(json.dumps({"query": question, "hits": hits}, ensure_ascii=False))
        return 0
    if not hits:
        # Silence would read as a failure of the command. Nothing scoring above
        # zero is an answer about the wiki: these words are not in it.
        print(f"No page carries the words of {question!r}.")
        return 0
    for hit in hits:
        where = f"{hit['page']}:{hit['line']}" if hit["line"] else hit["page"]
        print(f"{where}  {hit['title']}")
        if hit["heading"]:
            print(f"    {hit['heading']}")
        text = str(hit["text"])
        if text:
            print(f"    {text[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
