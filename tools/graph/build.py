#!/usr/bin/env python3
"""Build an offline graph beside the configured index and report wiki quality."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.graph.build_nodes import build_nodes
from tools.graph.link_components import link_components
from tools.graph.print_related import print_related
from tools.graph.scan_pages import scan_pages
from tools.graph.undirected_neighbours import undirected_neighbours
from tools.index.data_directory_not_found_error import DataDirectoryNotFoundError
from tools.index.find_data_directory import find_data_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.ordered_page_directories import ordered_page_directories

LINK = re.compile(r"\[\[([^\]|#]+)")


def main(argv: list[str] | None = None) -> int:
    """Rebuild graph.html and print every graph-quality issue the walk found."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", metavar="PATH")
    args = parser.parse_args(argv)
    try:
        root = find_data_directory(args.data, os.environ, Path.cwd())
        config = load_syntopica_config(root, os.environ)
    except (DataDirectoryNotFoundError, InvalidSyntopicaConfigError) as error:
        print(str(error), file=sys.stderr)
        return 1
    output = config.index.with_name("graph.html")
    if output.is_symlink() or output == config.index or not output.resolve().is_relative_to(root):
        print("Graph output must be a separate file inside the data directory", file=sys.stderr)
        return 1
    pages = scan_pages(config.index.parent, ordered_page_directories(config.pages))

    edges: list[list[str]] = []
    dangling: list[tuple[str, str]] = []
    self_links: list[str] = []
    inbound: dict[str, list[str]] = {pid: [] for pid in pages}
    for p in pages.values():
        for t in dict.fromkeys(p["targets"]):  # dedup, keep order
            if t not in pages:
                dangling.append((p["id"], t))
            elif t == p["id"]:
                self_links.append(p["id"])
            else:
                edges.append([p["id"], t])
                inbound[t].append(p["id"])

    neighbours = undirected_neighbours(pages, edges)
    nodes = build_nodes(pages, inbound)

    orphans = sorted(n["id"] for n in nodes if n["in"] == 0)
    dangling_pairs = sorted(set(dangling))
    data = {
        "nodes": nodes,
        "edges": edges,
        "dangling": dangling_pairs,
        "orphans": orphans,
    }

    template = (Path(__file__).resolve().parent / "viewer.html").read_text(encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        template.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False)),
        encoding="utf-8",
    )
    indexed = {
        t.strip()
        for t in LINK.findall(config.index.read_text(encoding="utf-8"))
        if "/" in t.strip()
    }
    unindexed = sorted(set(pages) - indexed)
    print(
        f"pages {len(nodes)}  links {len(edges)}  orphans {len(orphans)}  "
        f"dangling {len(dangling_pairs)}  unindexed {len(unindexed)}"
    )
    print(f"wrote {output}")
    for source, target in dangling_pairs:
        print(f"  dangling: {source} -> [[{target}]]")
    for pid in unindexed:
        # Named with who does link there: the index is the one place a page is
        # reachable from without already knowing it exists, so a page missing
        # from it is found only by whoever already found it.
        linked_from = ", ".join(inbound[pid]) or "nothing"
        print(f"  not in index.md: {pid} (linked from {linked_from})")
    for target in sorted(indexed - set(pages)):
        print(f"  index.md links nowhere: [[{target}]]")
    for pid in sorted(set(self_links)):
        print(f"  self-link: {pid}")
    for pid in sorted(n["id"] for n in nodes if n["out"] == 0):
        print(f"  links to no other page: {pid}")
    components = link_components(neighbours)
    for members in components[1:]:
        print(f"  cluster reachable from nothing else: {', '.join(members)}")
    print_related(pages, neighbours)
    return 0


if __name__ == "__main__":
    sys.exit(main())
