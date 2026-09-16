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

The engine never runs inside your data: this repository is one checkout, your
wiki is a directory of its own, and one file, `syntopica.config.json`, tells
the engine where the pages are. The quickest route is the
[Syntopica hub](https://github.com/syntopica/syntopica), which writes that file
and the directories the schema expects:

```bash
uv tool install git+https://github.com/syntopica/syntopica
mkdir -p wiki/engines && cd wiki
git clone https://github.com/syntopica/brain.git engines/brain
(cd engines/brain && uv sync)
syntopica init --with brain
cat > pages/start.md <<'PAGE'
---
title: Start
type: concept
updated: 2026-09-16
summary: 'The starting point for this wiki.'
sources: []
---

Decisions live in [[pages/decisions]].
PAGE
cat > pages/decisions.md <<'PAGE'
---
title: Decisions
type: concept
updated: 2026-09-16
summary: 'Decisions recorded as linked pages.'
sources: []
---

Back to [[pages/start]].
PAGE
engines/brain/bin/brain index     # write index.md from your pages
engines/brain/bin/brain graph     # orphans, dangling links, related pairs; writes graph.html
engines/brain/bin/brain lint      # frontmatter, filenames, links that resolve
engines/brain/bin/brain doctor    # what is still missing, by name
```

Expect `index.md: 2 pages`, `pages 2  links 2  orphans 0  dangling 0`, zero
lint issues and a passing doctor. Links carry the page directory, as in
`[[pages/decisions]]`; a bare `[[decisions]]` is not read as a page link.

Without the hub, write `syntopica.config.json` by hand from
`schema/syntopica.config.example.json`, keeping only the `brain` and
`engines.brain` sections, and run `git init` in the data directory. `doctor`
then names every directory and file it still expects; today that includes a
`clips/` directory even when no clips engine is configured, because the
schema's default archive path must exist.

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
