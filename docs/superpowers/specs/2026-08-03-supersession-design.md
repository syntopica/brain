# Supersession - design

Status: **specified and built 2026-08-03.** The `TODO.md` entry it closes -
"Evaluate supersession fields" - was decided on the same day to be built _after_
the source-authority order, and the ordering is the decision's substance: which
of two beliefs is current reads as arbitrary until something has said which kind
of source outranks which.

## Why

`SCHEMA.md` has always said to name a contradiction rather than resolve it
silently, and since 2026-08-03 `contradictions:` makes an open disagreement
enumerable. Both are about a disagreement that is **live**: two sources say
different things and the page holds both.

Nothing covers the case where the disagreement is over. A clip arrives, the page
was wrong, the sentence is rewritten, and the wiki loses the only record that it
ever held the old belief. A reader a month later cannot tell a corrected belief
from one nobody ever examined, and the two want opposite things: the first is
settled, the second is a gap.

The 2026-08-02 ecosystem survey found three shapes for this and they do not
agree. `MauricioPerera` stores `supersedes` / `supersededBy` and hides
superseded facts from retrieval; `gbrain` keeps bitemporal `valid_from` /
`valid_until`; openwiki keeps a `## Contested` section labelled across every
affected page and explicitly **not resolved by recency alone**.

## The choice

openwiki's shape, for one reason: the other two hide the losing fact, and this
repository's rule is to name a contradiction rather than bury it. A field that
removes the old belief from retrieval is the same deletion the convention exists
to prevent, performed by the retrieval layer instead of by the author.

Body section rather than frontmatter, which is where it differs from
`contradictions:`. A superseded belief needs the sentence that explains why the
new one outranks; a one-line list entry cannot carry it, and the frontmatter of
a page that has corrected itself five times would be longer than the page.

## The convention

```
## Contested

- 2026-08-03: the page held X; it now holds Y, because <why Y outranks>.
```

Near the bottom of the page, just before `## Sources`. Never deleted, never
reordered away, never justified by recency - the authority order decides, the
same rule that decides a live disagreement.

## Where each piece lives

Three things, chosen so no single one has to be trusted alone.

**The prompt asks.** `SUPERSESSION_INSTRUCTION` is one constant shared by the
codex, agy and interactive prompts, for `CLAIM_MARKER_INSTRUCTION`'s reason: a
rule the gate enforces must not drift between the transports that have to
satisfy it. Adding it changes `promptSha256` on every future ledger, which is
what that field is for.

**Validation refuses.** `contestedRetainedFailure` fails a modification that
drops an entry the committed page carried. Judged on the committed page for
`reviewedPageFailure`'s reason - comparing the worktree with itself would let
one change delete a belief and its own record together. Retention, not
append-only: unlike `sources:`, nothing points at a contested entry's position,
so a run may sort or interleave freely. What it may not do is lose one.

**The audit reports what a tool can judge.** `findUndatedSupersessions` reports
an entry carrying no date. Whether Y really outranks X is prose only a reader
can weigh - the limit `findOpenContradictions` already states about which side
of a disagreement is which - but an undated entry records nothing at all.

Deliberately **not** enumerated: the section itself. Open contradictions are
listed in full because the set falls to zero when they settle; contested entries
are kept forever, so listing them would grow without bound and the reader would
learn to skip the section.

## Files

- `tools/clips/src/audit/page-contested-beliefs.ts` - the reader.
- `tools/clips/src/audit/find-undated-supersessions.ts` - the audit check.
- `tools/clips/src/validation/contested-retained-failure.ts` - the gate.
- `tools/clips/src/synthesis/supersession-instruction.ts` - the prompt fragment.
- Wired in `commands/audit.ts`, `audit/audit-finding.ts`,
  `audit/audit-check-headings.ts`, `validation/change-failure.ts`, and the three
  prompts.
- `SCHEMA.md` - the convention, next to `contradictions:` and the authority
  order.

## Tests

Unit tests for the reader (entries, a wrapped entry folded, stopping at the next
section, a page with no section) and the check (undated reported, dated silent,
no section silent). Two integration cases in
`validate-worktree.integration.test.ts`: a change that drops an entry is
refused, and one that appends an entry while keeping the old is accepted.

## What it is silent on today

Every page in the wiki. No page carries a `## Contested` section, so the check
reports nothing and the gate refuses nothing - the same grandfathering the
claim-level citation scheme accepted the same day. The convention starts
producing history with the next synthesis batch, not retroactively.

## Open questions

- **A belief superseded across several pages.** openwiki labels the contested
  claim on every affected page; nothing here checks that the labels agree, and
  the wikilink graph is the only thing that could find the other pages.
- **A contested entry whose reason is empty.** The audit checks the date, not
  the because-clause. Reading the clause for the recency wording ("newer",
  "latest") was considered and dropped: it is prose-matching, and the always-
  fires risk is worse than the miss.
