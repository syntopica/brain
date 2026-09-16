# syntopica/brain

The engine of an **LLM Wiki**: a compounding, git-versioned knowledge base of
synthesized, cross-linked Markdown pages, written and maintained by a model and
read by both people and agents. It is not a vector database, and there are no
embeddings in it. Knowledge is synthesized once into pages and kept current,
instead of being rediscovered from raw sources on every question.

This repository holds the **code**. Your pages, your captures and your own
scripts live in a data directory you own, and the two find each other through
one file, `syntopica.config.json`. Nothing here knows whose wiki it is running
against.

## What it does

- **`brain index`** rebuilds `index.md` from every page's `summary:` line, so
  the map is derived from the pages rather than maintained beside them.
- **`brain graph`** builds the link graph: orphans, dangling links, clusters
  reachable from nothing, and related-but-unlinked pairs scored by shared
  vocabulary. It writes an HTML viewer alongside the report.
- **`brain lint`** checks the conventions this engine enforces - frontmatter,
  filenames, links that resolve, summaries that exist.
- **`brain doctor`** answers whether this instance is set up: configured paths
  present, repositories where the configuration says, the API versions
  supported, the executables and credentials the commands need.
- **`tools/eval`** measures retrieval over your own wiki: a query set, keyword
  and PageRank scoring, and recall@k, so a change to the page conventions can be
  judged rather than argued about.

## Quick start

The engine never runs inside your data. Three checkouts side by side: this
repository, its sibling [`syntopica/clips`](https://github.com/syntopica/clips)
(the capture pipeline, which the configuration contract requires even before
you clip anything), and your own data directory, which must be a Git repository
of its own.

```bash
git clone https://github.com/syntopica/brain.git
git clone https://github.com/syntopica/clips.git
(cd brain && uv sync)

mkdir -p wiki/notes wiki/clips && cd wiki && git init
cat > syntopica.config.json <<'JSON'
{
  "schemaVersion": 1,
  "instanceId": "mine",
  "brain": {
    "pages": ["notes"],
    "sources": "sources",
    "index": "index.md",
    "ledger": ".ingest"
  },
  "clips": { "archive": "clips" },
  "engines": {
    "brain": { "path": "../brain", "apiVersion": 1 },
    "clips": { "path": "../clips", "apiVersion": 1 }
  }
}
JSON

../brain/bin/brain doctor          # what is missing, by name
../brain/bin/brain index           # write index.md from your pages
../brain/bin/brain graph           # orphans, dangling links, related pairs
```

On a fresh instance `doctor` exits 1 and names the directories and files it
still expects (`sources`, `.ingest`, the `.config/*.json` lists); `index` and
`graph` already work with one page under `notes/`.

Every command takes `--data PATH` to select an instance explicitly. Without it,
`SYNTOPICA_DATA` is used, and without that the commands walk upwards from the
working directory to the nearest `syntopica.config.json`, stopping at a
repository boundary so one instance can never be read while standing in another.

## The configuration contract

`schema/syntopica-config.schema.json` is the authority: a closed schema, so an
unknown key is an error rather than a setting that silently does nothing.
`schema/syntopica.config.example.json` is a complete instance to copy from.
Paths resolve relative to the file that declared them, which is what lets a
local override sit beside the tracked configuration without either one guessing
about the other. `syntopica.local.json`, when present, overlays the tracked file
and belongs in `.gitignore`.

`SCHEMA.md` is the page format the engine expects. `CLAUDE.md` is what a coding
agent working on this repository needs to know.

## Requirements

Python 3.12 or newer with [uv](https://docs.astral.sh/uv/), and Git.
`brain graph` writes a self-contained HTML file and needs no server.

## Licence

MIT. See `LICENSE`.
