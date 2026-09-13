# Claim-level citations - design

Status: **specified 2026-08-03, built the same day, all four milestones.** The
amendments below record where the build departed from the body; the body itself
is left as written. The owner decided on the same day to build the full
`kytmanov` shape - deterministic refs, a prompt gate, marker rewriting, a lint,
tests - rather than the cheaper marker-convention-only variant, which nothing
would enforce and which is the always-fires-or-never-fires shape this repository
has already switched off once.

This is the keystone of the provenance lane in `TODO.md`. Three entries wait on
it: quote grounding, the citation half of the pre-commit validator, and the
grader's open question about a claim that is true but outside the page's own
sources. It is the only one of the four that can be built without another
decision first.

## Why

Provenance here is page-level and lives in frontmatter: `sources:` says where a
page came from, and nothing says where a _sentence_ came from. Two costs follow,
both measured rather than assumed.

**The grader cannot tell "unsupported" from "not from a source".** Grading
`business/pyfirma.md` three times on 2026-08-02 produced one unsupported claim
per pass, and each fix produced the next: "hard-to-automate Java dependency",
then "official validator", then "the official **Spanish** e-signature
application" - a fact no reader here doubts and the repository README simply
does not state. Every claim is graded against that page's own `sources:`, so a
page mixing one cited source with the owner's own knowledge reports forever, and
the fixes get worse: the third would have deleted a true fact to satisfy a scope
rule.

**The authority order has a rank nothing can reach.** `SCHEMA.md` ranks the
owner's own knowledge above every other source, and `SOURCE_AUTHORITY_TIERS`
carries `owner` as its first entry with a comment saying nothing returns it. A
`sources:` entry is a path or a url, so no page can say "this came from me". The
rank is written down so the order is not stated wrongly in the meantime; this
design is what makes it reachable.

## Non-goals

- **Not a requirement that every claim carry a marker.** A check that fires on
  every page carries no information: an inferred `reviewed:` fired on 86 of 90
  pages and was removed, and a `last_verified:` that demanded a date would have
  fired on all 49 non-exempt pages the day it shipped. The wiki-wide lint checks
  that markers _resolve_, never that they exist.
- **Not a backfill.** 110 pages exist and their prose cannot be attributed
  mechanically. They are grandfathered; the gate applies to what a synthesis run
  writes from now on.
- **Not a change to `sources:` shape.** Six readers parse that field today
  (`pageSources`, `pageSourceUrls`, `pageSourceFiles`, `resolveLocalSource`,
  `tierOfSource`, `frontmatterListLines`). A mapping form would rewrite all of
  them and all 110 pages to buy what append-only ordering buys for free.
- **Not retrieval.** Markers are provenance, not an index; the query eval lane
  in `TODO.md` is a separate piece of work.

## The reference scheme

A page's refs are **positional over its own `sources:` list**: the first entry
is `S1`, the second `S2`, and so on. Deterministic, derivable by any reader,
nothing stored twice.

One ref is not positional. **`OWN` is the owner's own knowledge** - the tier
`SOURCE_AUTHORITY_TIERS` already names and nothing has been able to return. It
is spelled as a word rather than `S0` on purpose: a numeric neighbour of `S1`
invites the typo that silently reattributes a claim, and the tier it maps to is
the one that outranks everything.

`OWN` is what closes the pyfirma loop. "The official Spanish e-signature
application" is a claim the owner knows first-hand and no clip states; today it
is unsupported forever, and with a marker it is attributed to the rank that
outranks the clip.

### Append-only sources

Positional refs have one hazard and it is worth naming rather than discovering:
reordering `sources:` silently changes what every marker on the page means.

So on a page that carries markers, `sources:` is **append-only**. A new entry
goes at the end; an existing entry may not be reordered or removed. Validation
refuses a synthesis that does either, comparing against the committed page - the
same way `reviewed: true` is judged on the committed page so one change cannot
delete the marker and the boundary together.

A page carrying no markers is unaffected, which is every page that exists today.

## Marker syntax

An author writes a bare marker at the end of the claim's sentence:

```markdown
Medium's Apollo state carries the full article body [S1]. The invoice numbering
restarts each calendar year [OWN].
```

Rewriting turns each into a link into the page's own `## Sources` section:

```markdown
Medium's Apollo state carries the full article body [[S1]](#sources).
```

The rewrite is mechanical and runs in the pipeline, not in the author's head,
for the reason the index map exists: a convention a person has to remember is a
convention that decays. It happens between validation and the review gate, in
the same slot `tools/index/build.py` occupies, so the reviewer approves the
rewritten text rather than approving one thing and publishing another.

## Where each piece lives

**Prompt gate.** Both synthesis prompts (`codexPrompt`, `agySynthesisPrompt`)
list the refs available for this clip - `S1..Sn` from the sources the page will
carry, plus `OWN` - and require every factual claim to end with one of them.
They must also state the thing that makes `OWN` honest rather than an escape
hatch: `OWN` is for what the wiki's owner knows first-hand, and a model must
never mark its own inference `OWN`. A claim it cannot attribute is a claim it
should not write.

**Validation.** `validateWorktree` gains two refusals on a page the run created
or modified: a marker naming an index with no matching `sources:` entry, and a
`sources:` list that was reordered or shortened rather than appended to. Both
leave the brain untouched, as every validation failure already does.

**Lint.** `clips audit` gains `unresolved-claim-ref`, reported for any page
whose markers name a source it does not have. Free to compute, runs over the
whole wiki, and reports nothing today because no page carries a marker - which
is the correct reading, not a broken check.

A second check, `uncited-source`, reports a `sources:` entry no marker cites,
**and only on a page that carries at least one marker**. On a grandfathered page
every source is uncited and the finding would be noise; on a page written under
this design it means a source was consulted and never used, or a marker was lost
in an edit.

**Grader.** `gradePrompt` learns the scheme, and this settles the open decision
recorded in `TODO.md`: a claim marked `OWN` is reported as **uncheckable**, not
passed silently and not reported as unsupported.

Uncheckable is a third state, next to `unsupported` and `clean`, and it does
**not** change the verdict: a page whose only findings are uncheckable claims
grades `clean`. That is the shape `verification: exempt` already uses - a state
that reads differently without firing - and it is what keeps the pyfirma loop
from simply moving to a new name. Passing an `OWN` claim in silence was the
alternative and it is worse: silence is exactly how an unverified page came to
look clean in the first place.

The count belongs in the report because it is the one number that says how much
of a page nothing here can check.

## Files

Following the atomic file rule; one export each.

```
tools/clips/src/citations/claim-ref.ts             type ClaimRef
tools/clips/src/citations/own-claim-ref.ts         const OWN_CLAIM_REF
tools/clips/src/citations/claim-ref-pattern.ts     the marker regex
tools/clips/src/citations/page-claim-refs.ts       markers in a page's prose
tools/clips/src/citations/refs-for-sources.ts      sources -> S1..Sn
tools/clips/src/citations/unresolved-claim-refs.ts markers naming no source
tools/clips/src/citations/rewrite-claim-refs.ts    bare marker -> anchored link
tools/clips/src/citations/tier-of-claim-ref.ts     ref -> SourceAuthorityTier
tools/clips/src/citations/append-only-sources.ts   committed vs proposed list
tools/clips/src/audit/find-unresolved-claim-refs.ts
tools/clips/src/audit/find-uncited-sources.ts
```

`pageClaimRefs` reads prose only. It must skip the frontmatter block and the
`## Sources` section, for the reason `gradePrompt` already gives: neither is a
sentence the page asserts, and reading one as a claim invents findings the page
does not contain. `linesOutsideCodeFences` is the existing helper for the third
exclusion - a marker inside a fenced block is sample text.

## Tests

- `refsForSources`: order, empty list, a single source.
- `pageClaimRefs`: markers found in prose; none read from frontmatter, from
  `## Sources`, or from inside a code fence.
- `unresolvedClaimRefs`: `S3` on a two-source page is unresolved; `OWN` is
  always resolved and never counted against the source list.
- `rewriteClaimRefs`: a bare marker becomes an anchored link; an already
  rewritten marker is left alone, because the pass runs on every ingest and must
  be idempotent.
- `appendOnlySources`: an append passes; a reorder, a deletion and a
  substitution each fail.
- `tierOfClaimRef`: `OWN` is `owner`; `S1` takes the tier of the source it
  points at, via `tierOfSource`.
- Integration: a synthesis writing `S9` on a one-source page is refused and the
  brain is untouched; a synthesis writing valid markers publishes them
  rewritten.
- Grade: a page whose only finding is an `OWN` claim grades `clean` with a
  non-zero uncheckable count.

## Milestones

1. **The scheme, read-only.** `refsForSources`, `pageClaimRefs`,
   `unresolvedClaimRefs`, `tierOfClaimRef`, plus the two `clips audit` checks.
   Ships with the wiki reporting nothing, which is the honest baseline.
2. **The gate.** Prompt changes, the two validation refusals,
   `appendOnlySources` against the committed page.
3. **The rewrite.** `rewriteClaimRefs` between validation and the review gate.
4. **The grader.** `uncheckable` as a third state, carried through
   `GradeResult`, `parseGradeOutput` and `formatGradeReport`.

Milestone 1 unblocks nothing else and is worth shipping alone; the quote
grounding entry in `TODO.md` becomes buildable after milestone 3, when a marker
identifies which source a quoted span belongs to.

## Open questions

- **What a marker means on a page an ingest merely edits.** A run that appends
  two sentences to a 200-line page can mark its own sentences and cannot mark
  the rest. Milestone 2 checks only what the run wrote, which is right, but it
  means a page will carry markers on some claims and not others for a long time
  - and `uncited-source` fires on exactly those pages. It may need to key on the
    claims the run touched rather than on the page.
- **Whether `OWN` needs to survive into `sources:`.** A page whose claims are
  all `OWN` cites nothing, so `findUnresolvedCitations` skips it and
  `verification: exempt` is what covers it today. That is consistent, but it
  means the marker and the frontmatter answer the same question in two places.

## Amendments

Append here with a dated heading rather than editing the body: source comments
cite this file by line number, and an insertion above them invalidates the
citation silently.

### 2026-08-03 - a fourth exclusion: inline code spans

Milestone 1 shipped and the body above names three exclusions for
`pageClaimRefs` - frontmatter, `## Sources`, and fenced code blocks. There is a
fourth, and leaving it out was not theoretical: the first run of `clips audit`
over the live wiki reported `S2` through `S51` as uncited sources on
[[topics/llm-wiki]], whose prose describes this very convention in `` `[S1]` ``.

So `pageClaimRefs` also strips inline code spans, through the existing
`withoutInlineCode`. It is the same pairing the maths checks already use one
nesting level apart, and for the same reason both give: a code span is markup
the renderer never reads as content, so a marker inside one is documentation of
the scheme rather than a citation under it. A page that documents a marker does
not cite one.

With it, both milestone-1 checks report nothing over the whole wiki, which is
the baseline the design predicted.

### 2026-08-03 - `uncited-source` fires on a page carrying only `OWN`

Not a change, a consequence worth stating before it is met. A page that lists
sources and marks every claim `OWN` carries at least one marker, so
`findUncitedSources` runs on it and reports every source as uncited - correctly
by the rule as written, and confusingly to a reader who marked the page
honestly.

It is left as is for milestone 1 rather than special-cased. The finding is real
under either reading - a page whose claims are all the owner's own knowledge
either does not need the sources it lists, or has claims that should have cited
them - and inventing an exception before a page like that exists would be
guessing at which. It belongs with the open question above about `OWN` and
`sources:` answering the same thing twice.

### 2026-08-03 - the prompt states the scheme, it does not list this run's refs

Milestone 2 shipped and the body above asks both synthesis prompts to "list the
refs available for this clip - `S1..Sn` from the sources the page will carry".
That is not computable when the prompt is built, and the reason is the design's
own: refs are positional over **the page's** `sources:` list, and the model
chooses which page it writes or updates. A page already carrying five sources
gives this clip `S6`; a new page gives it `S1`. The prompt cannot know which
until the model has decided.

So the three prompts carry `CLAIM_MARKER_INSTRUCTION`, a shared constant stating
the rule - positional over that page's own list, `OWN` for first-hand knowledge,
never `OWN` for the model's own inference, append-only sources on a marked page.
Derivable by whoever writes the page and checkable afterwards, which is what the
gate actually needs.

Three prompts rather than the two the body names. The interactive
`SYNTHESIS_INSTRUCTIONS` needs it as much as `codexPrompt` and
`agySynthesisPrompt`: validation refuses an unresolved marker whatever wrote the
page, and the interactive transport is the one a person drives, where a rule
nobody stated is a run that fails at the gate. One constant rather than three
copies, because a rule validation enforces must not drift between the transports
that have to satisfy it.

All three prompt hashes change, which is what `promptSha256` is for.

### 2026-08-03 - where the two refusals sit in the chain

Both live in `changeFailure`, after `pageContentFailure` rather than before it,
so a symlink or a binary is named as what it is instead of as a page carrying no
markers. `sourcesAppendOnlyFailure` reads the committed list through
`committedPageText` for the reason `reviewedPageFailure` already gives:
comparing the worktree copy against itself would let one change move a source
and rewrite the marker pointing at it in the same breath.

Both are silent on every page in the wiki today, since none carries a marker.

### 2026-08-03 - the rewrite has to reformat what it rewrote

Milestone 3 shipped. `[[S1]](#sources)` is eleven characters longer than `[S1]`,
and this repository's prettier wraps prose at eighty, so a rewrite that stopped
at rewriting would publish pages that fail the brain's own `pnpm run check` on
the next commit. That is not hypothetical: 15 clips landed on origin/main on
2026-08-02 with exactly that class of violation and left the gate red until a
manual sweep of 23 files.

So `rewriteClaimMarkers` reformats every page it changed, through the same
`formatWorktreePages` validation uses, and a prettier failure routes the clip to
needs-claude under `CLAIM_REWRITE_FAILED` rather than crashing the run. A page
nobody marked comes out byte-identical, so nothing is written and nothing is
formatted on it - which is every page the wiki had before the scheme.

One consequence, small and worth stating: `validateLimits` runs inside
validation, before the rewrite, so the changed-line counts are of the bare text
and the reflow is not counted against them. `formatWorktreePages` documents the
opposite ordering for its own pass; the rewrite cannot have it, because it must
run after validation has confirmed every marker resolves. The reviewer still
approves the rewritten text, which is the property that matters.

### 2026-08-03 - the rewritten form creates no dangling link

Checked rather than assumed, because `[[S1]](#sources)` opens with `[[` and two
readers here parse wikilinks. Both `tools/graph/build.py` and `wikilinkTargets`
drop a target containing no `/` as a root reference in the shape of
`[[SCHEMA]]`, so a rewritten marker is invisible to the graph and adds nothing
to the orphan count.

Idempotence is carried by a second, narrower pattern rather than by the reader's
one. `BARE_CLAIM_REF_PATTERN` refuses a marker already wrapped in an outer
bracket, so running the pass twice is the same as running it once - which it has
to be, since a page can be edited by many ingests. `CLAIM_REF_PATTERN` stays
deliberately wide and matches both forms, because the lint has to see a marker
whichever pass last touched the page.

### 2026-08-03 - `uncheckable` is a list of strings, and it is required

Milestone 4 shipped. Two shape decisions the body leaves open.

**Plain strings, not `{claim, why}`.** An unsupported claim needs a `why`
because the reason differs every time - a number the sources lack, a causal link
they do not draw. An uncheckable claim has the same reason on every entry: it is
marked `[OWN]`. A field whose value never varies is decoration, so `uncheckable`
carries the page's own words and nothing else.

**Required in both schemas, not optional with a default.** A grader that omits
the field has not said it found none, and treating an absent list as an empty
one would let a transport that ignored the schema read as a page with nothing
first-hand on it. Both transports impose the schema - `--output-schema` for
codex, `--json-schema` for agy - so a missing list means the output was not the
grader's, and `parseGradeOutput` returning null reads as `not graded`. That is
the honest failure, and it is the same principle `fallbackGraderAfterCodex`
follows: an ungraded page the operator knows about beats a graded-looking one.

**The report counts, it does not list.** Every uncheckable claim is uncheckable
for the same reason, so printing them all would bury the findings that need
reading. The count rides beside the evidence figure on `clean` and `unsupported`
alike, and is absent entirely when there are none, so a page under the old
scheme reads exactly as it did.

**`graderContradiction` is unchanged, deliberately.** A `clean` label over
uncheckable claims is not a contradiction - that is the design - and reading it
as one would turn every honestly marked page into `not graded`, which is the
always-fires failure in a new place.

### 2026-08-03 - quote grounding, the first consumer outside the scheme

The lane entry this design named as waiting on it is built:
`findUngroundedQuotes`, an eleventh `clips audit` check that takes a marked
quotation and asks whether the source that marker resolves to contains it.

The marker is what made it possible, and the reason is worth stating because it
is the argument for the whole scheme. Without one, grounding a quotation means
searching every source the page lists and reporting a miss only when all of them
lack it, which turns one page's evidence into a wiki-wide guess. With one, the
check has a single file to open.

Three shape decisions the check needed and this design does not cover.

**Attribution is to the first marker to the right of the closing quote, on the
same line.** The convention puts a marker after the claim it supports, so a
quotation with no marker after it is unattributed rather than attributed
backwards - and dropping it is right, because guessing a source invents the
evidence the check exists to verify.

**A quotation is six words or more.** Measured on the live wiki: 521 quoted
spans, 243 of one word and 467 of five or fewer. Those are UI strings, flags,
field names and terms held at arm's length - the wiki's own vocabulary, which no
source is expected to contain verbatim. Below the floor a quotation is not
exempt from being accurate; it is simply not distinguishable from emphasis by
anything mechanical.

**Comparison is normalized, never fuzzy.** Case, whitespace, and the typography
a publisher and this repository's ASCII text hygiene rule spell differently. The
words are left alone: a dropped, added or changed word is precisely what the
check is for.

It is silent on the whole wiki today, like the two lint checks it joins, and for
the same reason - no grandfathered page carries a marker. What it waits on now
is the corpus, not the design.

### 2026-08-11 — `uncited-source` skips half-marked pages

The half-marked-page prediction in the open questions fired, and at scale: the
2026-08-08/11 X tab sweeps appended marked sentences to three grandfathered
pages, which made the pages "marked" and turned every pre-scheme source on them
into a finding — 175 across `topics/claude-code-practice`,
`topics/dev-environment` and `topics/seo-playbook`, none of them a consulted
source left unused and none a lost marker.

The per-run answer the open question sketches — keying on the claims a run
touched — needs run data an offline audit does not have, so the check keeps its
page-level shape and adds a page-level discriminator instead: **a finding is
reported only when the page carries at least as many distinct claim markers as
it has uncited sources.** The two populations separate cleanly on that axis. The
check's real failures leave a few gaps on a well-marked page; a half-marked page
is a few markers against many gaps. Distinct markers, so a single source cited
many times does not vouch for a whole page; and `OWN` counts as a marker,
because it puts a claim under the scheme without citing — a one-claim `OWN` page
listing a source nothing cites is still the check's canonical finding, not a
half-marked page.

What is deliberately given up: a lost marker on a page with more gaps than
markers goes unreported until the page's marking catches up. That silence is the
same one the grandfathering rule already accepts, and the gate — which sees the
run's own diff — remains the place where a per-run check could hold appended
sources to their appended claims.

### 2026-08-24 — `sources:` is append-only, and the wrong-source error has no offline check

The convention this spec defines is positional: `S1` is the first `sources:`
entry, `S2` the second. That makes an insertion anywhere but the end a silent
renumbering of every marker below it, and the failure it produces is invisible
to `unresolvedClaimRefs` — the marker still resolves, it just resolves to the
wrong source. `S30` on a 28-entry page is reported; `S25` where `S27` was meant
is not, and it is the commoner of the two.

Measured on 2026-08-24: 20 of the 26 grade findings on
`topics/claude-skills-ecosystem.md` were this, all traceable to two entries
prepended to `sources:` after the markers beneath them were written. Renumbered
by hand against the grader's report. This is the 2026-08-08 index shift arriving
from the other direction — that one was a dropped read, this one an insertion.

Two consequences, one shipped and one still open:

- The rule now lives in `SCHEMA.md` next to the `sources:` format: append, never
  prepend or insert, and if an entry must go earlier, renumber the body in the
  same edit and say so in the commit message.
- The audit cannot close the gap offline, but the grade prompt already resolves
  every marker to decide support, so it is the one pass that could report
  `marker points at the wrong source` as its own finding class rather than
  emitting it as unsupported prose. Not built; recorded here so the next change
  to the grade prompt has the reason in front of it.
