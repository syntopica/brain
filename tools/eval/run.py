#!/usr/bin/env python3
"""Score the wiki's retrieval against the hand-written question set.

    python3 tools/eval/run.py [--data PATH]

Two model-free baselines, both reading only what is on disk: keyword scoring
over the pages' own words, and Personalized PageRank over the wikilink graph
seeded from those keyword hits. Recall@5, because five is the number SCHEMA.md's
query discipline allows a reader to open - which until this ran was a heuristic
with nothing behind it.

What it measures is retrieval, not answering. A wrong answer drawn from exactly
the right pages scores 1.0 here, and `expected_contains` / `expected_refusal`
over real prose need a model and a command this repository has not decided to
build (see docs/superpowers/specs/2026-08-04-wiki-eval-design.md). The refusal
rows below are the retrieval half of that question only: nothing found is the
correct answer, and a baseline that returns pages anyway scores zero.

Exit 0 for any score. This reports a number to read, not a gate to pass: a
low score may be a finding about the wiki's cross-linking rather than about the
runner, and failing a commit on it would be the always-fires shape this
repository has switched off once.
"""

import argparse
import os
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from keyword_scores import keyword_scores
from load_pages import load_pages
from pagerank_scores import pagerank_scores
from recall_at_k import recall_at_k
from top_pages import top_pages

from tools.index.data_directory_not_found_error import DataDirectoryNotFoundError
from tools.index.find_data_directory import find_data_directory
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.ordered_page_directories import ordered_page_directories

# The pages and the question set both belong to an instance, not to this
# engine. The instance is selected the way every brain command selects it
# (`--data`, then SYNTOPICA_DATA, then an upward walk), and its configured page
# directories are what gets scored: SYNTOPICA_DATA used to be read here as the
# pages root itself, so the instance root every other command takes scored only
# the refusal rows (recall@5 0.09, measured 2026-09-25). SYNTOPICA_EVAL_QUERIES
# names the instance's own ground truth; the bundled `queries.toml` is an
# example set.
QUERIES = Path(
    os.environ.get("SYNTOPICA_EVAL_QUERIES") or Path(__file__).resolve().parent / "queries.toml"
)
K = 5


def main(argv: list[str] | None = None) -> int:
    """Score both baselines over `queries.toml` and print recall@K.

    Prints a line per question either baseline failed, then the mean per
    baseline. Returns 0 whatever the score: this reports a number, it does not
    gate. Only a missing or invalid instance returns 1.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", metavar="PATH")
    args = parser.parse_args(argv)
    try:
        root = find_data_directory(args.data, os.environ, Path.cwd())
        config = load_syntopica_config(root, os.environ)
    except (DataDirectoryNotFoundError, InvalidSyntopicaConfigError) as error:
        print(str(error), file=sys.stderr)
        return 1
    pages = load_pages(config.index.parent, ordered_page_directories(config.pages))
    queries = tomllib.loads(QUERIES.read_text(encoding="utf-8"))["query"]
    totals = {"keyword": 0.0, "pagerank": 0.0}
    for query in queries:
        keyword = keyword_scores(query["question"], pages)
        entry = top_pages(keyword, K)
        # Seeded from the hits, not from every page carrying one of the words.
        # Measured on the first run: seeding with the full score vector returned
        # the same five hubs for every question, access-map and repo-catalog
        # among them, because a diffuse restart plus 30 iterations is graph
        # centrality with the question washed out of it.
        seed = {page_id: keyword[page_id] for page_id in entry}
        ranked = {
            "keyword": entry,
            "pagerank": top_pages(pagerank_scores(seed, pages), K),
        }
        for baseline, retrieved in ranked.items():
            score = recall_at_k(retrieved, query["expected_pages"])
            totals[baseline] += score
            if score == 1.0:
                continue
            missed = [page for page in query["expected_pages"] if page not in retrieved] or [
                "(nothing should have been returned)"
            ]
            print(f"{baseline} missed {', '.join(missed)}: {query['question']}")
            print(f"  returned: {', '.join(retrieved) or 'nothing'}")
    print(f"\n{len(queries)} questions, recall@{K}")
    for baseline, total in totals.items():
        print(f"  {baseline}: {total / len(queries):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
