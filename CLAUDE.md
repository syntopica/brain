# CLAUDE.md

Instructions for a coding agent working on this repository. `SCHEMA.md` is the
page format the engine enforces; `README.md` is what the engine does. This file
is about changing it.

## The one rule this project exists to keep

**No instance data in the engine.** Not a hostname, not an archive path, not an
account profile, not the subject scope a screening model is handed, not a
person's name in a test fixture. Every one of those is configuration: it belongs
in `schema/syntopica-config.schema.json` and in the instance's
`syntopica.config.json`, and the code reads it at call time, never at import.

The engine was split out of a private wiki, and every value now in the schema
was once a literal in a source file. The guard is
`tests/test_no_personal_identifier_in_engine.py`: it greps the tracked tree
against a pattern file supplied through `SYNTOPICA_PERSONAL_DATA_PATTERNS` and
names every file that matches. It skips silently when the variable is unset,
which is what lets a contributor run the suite without one while a release still
checks.

Two consequences worth stating, because both were learned the expensive way:

- **A default is a value.** `Path.home() / "p/archive"` is an instance detail
  with a friendly face; it works on exactly one machine and fails silently
  everywhere else, because the directory simply is not there and the command
  reports zero of whatever it counts.
- **Tests must not discover the developer's machine.** A public suite that walks
  to a home directory, an account profile or a live archive passes for its
  author and for nobody else. Build a synthetic instance with `tmp_path`.

## Files

One exported unit per file, one responsibility per unit, and every dependency an
explicit import. A helper gets its own file rather than living beside its
caller. `codeality-py` enforces this: BPY001 is one primary unit per module and
BPY002 is that the unit matches the file name, with a `[roles]` declaration in
`codeality-py.toml` for a script whose unit is `main`.

Prefer a role to a suppression. A role explains what a file is; a suppression
silences the question.

## Configuration

`schema/syntopica-config.schema.json` is the authority, and it is closed:
`additionalProperties: false`, so an unknown key is an error rather than a
setting that quietly does nothing. Add the key to the schema first, with its
default, then the loader, then the consumer.

Paths resolve relative to the file that declared them. That is what lets an
untracked `syntopica.local.json` hold an absolute path beside a tracked
`syntopica.config.json` holding a relative one, with neither guessing about the
other.

Instance selection is `--data`, then `SYNTOPICA_DATA`, then an upward walk from
the working directory that stops at a repository boundary. The boundary is the
point: without it a command run inside one instance can silently read another.

## Checks

```bash
uv sync
uv run codeality-py gate        # ruff, ruff format, mypy, baseline, deptry, pip-audit, pytest
uv run pytest -q
```

A change is finished when the gate passes, not when the code looks right. State
the command you ran and what it said.

## Prose

English, in code, comments, commit messages and documentation. Comments explain
why, and are worth writing exactly where the reason is not reconstructible from
the code: a measured number, a failure that cost a session, a rule that looks
arbitrary until you know what it prevents. A comment restating the line above it
is noise.

Commit messages are conventional (`feat(index): ...`, `fix(graph): ...`) and say
what changed and what verified it.

<!-- tadu:rule v1 -->
## Continuous TODO, Work Log, and History Coverage

Maintain `TODO.md` as the active backlog and `TODO_LOG.md` as the searchable
record of closed work. Use `TODO_HISTORY_INDEX.jsonl` to avoid parsing unchanged
conversations more than once.

- Read `TODO.md` at the beginning and end of related work. Search `TODO_LOG.md`
  before reopening an old task or repeating a previous solution.
- Record actionable bugs, risks, blockers, deferred work, missing tests,
  validation, documentation, and product improvements as they are discovered.
- Update an existing entry instead of creating a duplicate. Keep entries concise
  and under the most relevant category.
- Use `[ ]` pending, `[~]` partial or unverified, `[!]` blocked, `[x]` verified
  complete, `[-]` obsolete or superseded. Keep blockers in `TODO.md` and name
  the smallest action required to unblock them.
- When work becomes `[x]` or `[-]`, append a dated entry with concise result and
  evidence to `TODO_LOG.md`, then remove it from the active backlog. Keep one
  log file, grouped by year and month.
- Before reviewing past conversations, consult the history index and skip
  unchanged records already marked `complete` or `irrelevant`. Update a record
  only after its findings are reconciled; interrupted work stays `partial`.
- Do not interrupt the active task for unrelated non-critical work, and do not
  implement unrelated TODO items unless requested. Immediately report critical
  security, destructive, or data-loss findings.

Format: tadu spec v1. Workflows: the tadu-create and tadu-work skills.
<!-- /tadu:rule -->
