# SCHEMA - the page format this engine enforces

An LLM Wiki is a persistent, compounding knowledge base: synthesized,
cross-linked Markdown written and revised by a model, read by both people and
agents. There are no embeddings in it, and nothing is re-derived from raw
sources on every question. This file is the format the engine expects; the
conventions below are what `brain lint`, `brain index` and `brain graph` read.

## The three layers

1. **Raw sources** - the original documents, exports, transcripts and captures.
   Immutable, under the instance's `brain.sources` directory, or pointers to
   where they really live. Never edited by the wiki.
2. **The wiki** - the linked Markdown pages in the instance's `brain.pages`
   directories. The model writes and revises these.
3. **This schema** - the conventions every page follows, and the only thing the
   engine knows about your subject matter.

Which directories hold pages is per instance: `brain.pages` in
`syntopica.config.json` lists them, and nothing in the engine assumes a name.

## Page conventions

One file is one entity or topic, named `kebab-case.md`.

### Frontmatter

Every page opens with it:

```yaml
---
title: <human title>
type: <one of the instance's page types>
updated: <YYYY-MM-DD> # an absolute date, never "today"
summary: '<one line - what this page is, as the index lists it>'
reviewed: true # optional - curated; the pipeline may not edit it
verification: exempt # optional - nothing here can check this page
last_verified: <YYYY-MM-DD> # optional - when a person last checked it
contradictions: # optional - one line per open disagreement
  - <what disagrees with what, both sides named>
sources: # provenance, append-only
  - <path or URL>
---
```

`summary:` is required, single-quoted and on one line, because the root index is
**generated from it**: `brain index` owns the section lists and rewrites them
from the pages. Editing an index bullet by hand is work the next generation
throws away, so write the summary on the page and let the map follow.

`reviewed: true` marks a page as curated: an ingest refuses any synthesis that
modifies it, judged on the committed page so that one change cannot delete both
a page's protection and its content. It is opt-in - inferring the same thing
from Git history fires on nearly every page and carries no information.

`verification: exempt` says **nothing in this repository can check this page**,
and that this is deliberate. A page whose evidence lives in another repository,
a bank or a public register has nothing on disk for a claim to be true or false
against; a grader pointed at one reports forever, which is the always-fires
shape that gets a check switched off. Declared rather than inferred, so the
three states - clean, not graded, exempt - do not read the same.

`last_verified:` says when a person last read the page against the thing it
describes. It is a different question from `updated:`, which moves on any edit
and makes a page look current the moment one sentence changes. A page without
the field is silent: requiring it of every page would fire on all of them the
day the check ships.

`contradictions:` holds only what is **still open** - one line per disagreement,
both sides named. A rule to name a contradiction rather than resolve it silently
works at write time and nowhere else: a month later the sentence is somewhere in
a paragraph and nothing can list what is unresolved. The field makes it
enumerable.

### Granularity: hubs first, pages when there is no hub

Topic material is organised as a small set of **thematic hub pages** where new
findings accumulate as sections, one `## <finding>` per source. A finding
graduates to its own page when it has three or more independent sources, or when
something in the instance actively uses it; the hub then keeps a one-line
pointer. That keeps the root index readable at any intake volume.

The threshold governs graduating **out of** a hub, not entry into the wiki:

1. A hub covers the subject - the finding is a section in that hub, whatever its
   source count. One source is enough; hub-first is not a quota.
2. No hub covers it - the finding gets its own page. Do not invent a hub for a
   single finding: a hub with one section is a page with a misleading name, and
   it makes the graduation rule unmeasurable.
3. A second related finding arrives - that is when the hub appears, and the
   standalone page folds into it or becomes it.

### Sources, citations and authority

**`sources:` is append-only.** Add an entry at the end; never prepend one and
never insert one in the middle. Claim markers are positional - `[S1]` is the
first entry, `[S2]` the second - so an entry anywhere but the end silently
renumbers every marker below it, and the page then cites the wrong source while
every offline check still passes. A tool can report a marker past the end of the
list; it cannot report `S25` where `S27` was meant, which is the commoner error
and the one nothing sees. If an entry genuinely has to go earlier, renumber
every marker in the body in the same edit and say so in the commit message.

**Source authority, strongest first: the reader's own knowledge, a primary
source, an ordinary web page, a social post.** When two sources disagree, both
are recorded and neither is dropped, and the higher-ranked one is stated as
current - **never by recency**. A primary source is the thing itself: a
repository, an official record, a bank, a register, which in practice is every
`sources:` entry that is a path rather than a URL. A social post ranks last for
what it is, not for being wrong: unedited, unretractable, and usually one
person's reading of something that has its own URL.

The authority order is prose for a reader to apply, not the order of the list.
The list stays in arrival order, for the positional reason above.

### A replaced belief is versioned, never overwritten

When the wiki changes its mind, the old belief moves to a `## Contested` section
near the bottom of the page, one dated entry per replacement:

```markdown
## Contested

- 2026-01-31: the page held X; it now holds Y, because <why Y outranks X>.
```

This is the other half of `contradictions:`, not a second spelling of it. That
field holds a disagreement that is still open and is dropped when it settles;
this holds one that has settled, and is kept forever - a reader a month later
needs it to tell a corrected belief from one nobody ever examined. Whether Y
really outranks X is prose only a reader can weigh, and never by recency.

### Body anatomy

A one-paragraph summary first, so a reader gets the gist in a few seconds, then
the detail sections, then `## Contested` when the page has one, then a
`## Sources` list at the bottom.

Maths goes in `$$` blocks on their own lines. Inline `$...$` is not used: these
pages are read as Markdown on surfaces that do not render it, and a formula that
degrades into stray dollar signs mid-sentence is worse than one on its own line.

### Links

`[[dir/page-name]]` links a page by its path from the data directory, without
the extension: `[[pages/decisions]]` for `pages/decisions.md`. The graph and
lint scanners ignore a target with no `/` in it, so a bare `[[page-name]]`
creates neither an edge nor a dangling-link warning.
`brain graph` reads them: a link to a page that does not exist is reported as
dangling, a page nothing links to is an orphan, and a cluster reachable from
nothing else is reported as its own component. A new page that only the index
links to still counts as an orphan - connect it from the page it serves, or do
not write it yet.

## What the engine checks

| Command        | Answers                                                                     |
| -------------- | --------------------------------------------------------------------------- |
| `brain index`  | the root map, regenerated from every page's `summary:`                      |
| `brain graph`  | orphans, dangling links, components, related-but-unlinked pairs             |
| `brain lint`   | frontmatter, filenames, summaries, links that resolve                       |
| `brain doctor` | configured paths, repositories, API versions, executables, credentials      |
| `tools/eval`   | retrieval quality over your own pages: keyword and PageRank scoring, recall |

`brain index --check` exits non-zero when the committed map is stale, which is
what makes it safe to run in a gate rather than only by hand.

## Privacy

The engine holds no instance data. Your pages, your captures, your ledger and
your own scripts live in the data directory, which is yours to keep private, and
the configuration file is the only thing that points one at the other. Anything
that identifies you - hostnames, archive locations, account profiles, the
subject scope a screening model is given - is configuration, never code. A
contribution that hardcodes one is the one change this project will always
refuse.
