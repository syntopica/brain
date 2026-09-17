#!/usr/bin/env python3
"""Regenerate the configured index from page summaries, or check for drift."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.index.data_directory_not_found_error import DataDirectoryNotFoundError
from tools.index.find_data_directory import find_data_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.normalized import normalized
from tools.index.ordered_page_directories import ordered_page_directories
from tools.index.rendered import rendered


def main(argv: list[str] | None = None) -> int:
    """Write the selected index, or return one if --check finds a stale map."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", metavar="PATH")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = find_data_directory(args.data, os.environ, Path.cwd())
        config = load_syntopica_config(root, os.environ)
    except (DataDirectoryNotFoundError, InvalidSyntopicaConfigError) as error:
        print(str(error), file=sys.stderr)
        return 1
    directories = ordered_page_directories(config.pages)
    text = rendered(config.index.parent, directories, config.inbox)
    if args.check:
        current = config.index.read_text(encoding="utf-8")
        if normalized(current) == normalized(text):
            return 0
        print(
            "index.md is out of date; run python3 tools/index/build.py --data " + str(root),
            file=sys.stderr,
        )
        return 1
    config.index.parent.mkdir(parents=True, exist_ok=True)
    config.index.write_text(text, encoding="utf-8")
    print(f"index.md: {sum(len(list(directory.glob('*.md'))) for directory in directories)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
