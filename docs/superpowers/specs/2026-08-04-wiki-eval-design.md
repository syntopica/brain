# Evaluating the wiki - runner sizing

Status: **sized 2026-08-04, nothing built.** The `TODO.md` evaluation lane opens
with its own prerequisite - "size the runner before writing the questions" -
because an eval set written against a runner that does not exist is a document
nobody can run. This is that sizing, and it ends in a decision the owner owns.

## Why

`tools/clips` has 1952 tests and the wiki has none. Nothing here has ever
measured whether a question this wiki should answer gets answered, or whether
the reader lands on the right pages to answer it. Three of the four entries in
the lane - `kytmanov`'s `queries.toml`, `green-dalii`'s `eval-recall.ts`,
`kytmanov`'s `compare/` module - assume a command that takes a question and
returns something scoreable. This repository has no such command.

## What retrieval actually is here

There is no retrieval engine. `SCHEMA.md`'s query discipline is a human
instruction: start at `index.md`, open at most about five candidate pages, read
frontmatter and the summary first, follow `[[links]]` only as deep as the
question needs. The reader is Claude in a session, and the wikilink graph is the
index.

Measured today (`python3 tools/graph/build.py`): 110 pages, 542 links, 0
orphans, 0 dangling, and **14 pages that link to no other page**. That last
number is the one that matters for a link-following reader: a walk that lands on
`projects/project-after` cannot continue, so recall for any question those pages answer
is bounded by whether `index.md` or an inbound link pointed there in the first
place.

## The split that makes it affordable

**Retrieval is measurable without a model. Answering is not.** Everything below
follows from that one line, and it is why this is two runners rather than one.

### Tier 1 - free, scriptable, runnable on every batch

A `tools/eval/` runner scoring model-free baselines against a hand-written
ground truth of `question -> expected_pages`:

- **Keyword scoring** over page text - the closest thing to what a reader does
  when they scan `index.md` summaries.
- **Personalized PageRank over the wikilink graph**, seeded from the keyword
  hits, which is `green-dalii`'s own comparison and the only one that scores the
  graph rather than the prose.

Scored as recall@5, because five is the number `SCHEMA.md` already tells the
reader to respect. That heuristic has never had a number behind it; this is what
gives it one, and it is the cheapest result in the lane.

No model, no network, no quota. The graph and the page text are on disk, and
`tools/graph/` already parses both - `frontmatter_sources.py` and
`link_components.py` are reusable as they stand.

### Tier 2 - metered, and it needs a command that does not exist

`expected_contains` and `expected_refusal` are properties of an **answer**, not
of a page set. `expected_refusal` is the one worth the most - it tests that the
wiki says "not in the wiki" instead of inventing - and it cannot be scored
without a model producing prose.

That needs `clips query`: a command that takes a question, walks the wiki with a
model under the five-page discipline, logs every page it opened, and returns the
answer with that log. The log is not optional - without it Tier 2 measures only
whether the answer is right, and a right answer from the wrong pages is the
failure this lane exists to find.

Driving an in-session Claude instead was considered and does not work: nothing
outside the session can observe which files it read, so the page-open half is
unrecoverable. The harness has to be the thing doing the reading.

## Ground truth

About 30 questions, hand-written, spread across the five page directories, each
with the pages that should answer it. Two categories the set must carry beyond
the obvious ones: a question the wiki deliberately cannot answer (for
`expected_refusal`), and a question whose answer lives on a page that links
nowhere, since those 14 are where link-following retrieval is weakest by
construction.

Hand-written, not generated. A question set generated from the pages measures
whether the generator read the same page twice.

## What Tier 1 cannot say

Stated here so the number is not read for more than it is worth.

- Recall against an author-written ground truth measures the graph against one
  person's idea of the right pages, not against what a reader needed.
- A wrong answer from the right pages scores perfectly.
- The 14 dead-end pages cap link-following recall whatever the runner does, so a
  poor score may be a finding about the wiki's cross-linking rather than about
  retrieval - which is useful, and is not what the number claims to measure.

## The decision the owner owns

**Whether `clips query` should exist at all.** Today the reader is Claude in a
session, with the whole conversation as context; a query command is a second,
poorer reader that exists to be scored. Building it changes what this repository
is, and that is not a call an eval makes on its own.

Tier 1 does not wait on that decision and is the recommended first step: it is
free, it scores the discipline `SCHEMA.md` already states, and if it reports
that the graph retrieves badly, that is worth knowing before anything metered is
built.

## Rough size

- Tier 1: the runner, two baselines, the loader and a report - a day, no quota.
- The ground-truth set: about two hours, and it is the part that cannot be
  automated.
- Tier 2: `clips query` plus its page-open log, then the scorer. Not sized
  further until the decision above is made, because the command's shape decides
  most of it.
