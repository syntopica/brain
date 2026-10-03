"""Print one page as a document, refusing ids outside the page roots."""

import argparse
import json

from tools.graph.scan_pages import scan_pages
from tools.index.ordered_page_directories import ordered_page_directories
from tools.index.page_document import page_document
from tools.index.page_path import page_path
from tools.index.syntopica_config import SyntopicaConfig
from tools.index.valid_page_id import valid_page_id

SCHEMA_VERSION = 1


def brain_page(config: SyntopicaConfig, arguments: list[str]) -> int:
    """Print the page document, or an error document with a fixed code.

    An id that is malformed and an id that names no page inside a root fail
    differently, so a caller can tell a bad request from a missing page.
    """
    parser = argparse.ArgumentParser(prog="brain page", description=__doc__)
    parser.add_argument("--json", action="store_true", required=True)
    parser.add_argument("--id", required=True, dest="page_id")
    args = parser.parse_args(arguments)
    directories = ordered_page_directories(config.pages)
    root = config.index.parent
    path = page_path(args.page_id, root, directories)
    if path is None:
        code = "page_not_found" if valid_page_id(args.page_id) else "invalid_page_id"
        print(json.dumps({"schemaVersion": SCHEMA_VERSION, "error": code}))
        return 1
    document = page_document(args.page_id, path, scan_pages(root, directories))
    print(json.dumps(document, ensure_ascii=False))
    return 0
