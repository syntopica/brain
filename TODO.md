# Open work

> Consolidated from the accessible agent conversation history of this
> project. Last reviewed: 2026-10-12. History coverage: Partial. Not re-audited
> during the 2026-10-12 format migration.
>
> States: `[ ]` pending · `[~]` partial or unverified · `[!]` blocked · `[x]`
> verified complete · `[-]` obsolete or superseded. Closed work moves to
> `TODO_LOG.md`.

## Index

- [ ] 2026-10-28 — **Index:** Strip YAML block-scalar indicators from page summaries.
  - Observation: a page whose frontmatter stores `summary: >-` (or `>`, `|`, `|-`) is listed in the generated index as `— >- <text>`, because `folded_value` joins the continuation lines but keeps the indicator, and `summary_of` only removes quotes.
  - Evidence: `brain index` on an instance page with `summary: >-` reproduced the literal `>-` in `index.md`, 2026-10-28.
  - Next step: in `tools/index/summary_of.py` (or `folded_value.py`), drop a leading block indicator (`[>|][+-]?`) before unquoting, and add a test with a folded summary.
