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

<!-- tadu:rule v4 -->

## Continuous TODO, Work Log, and History Coverage

Keep the active backlog and the searchable record of closed work with tadu. A
repository uses `TODO.md` and `TODO_LOG.md` (format 1), or one JSON file per
task under `todo/` (format 2, when `todo/tadu.json` exists). Use
`TODO_HISTORY_INDEX.jsonl`, when present, to avoid parsing unchanged
conversations more than once.

- Do not read the backlog files whole: query them. `tadu list` filters with
  `--category`, `--type`, `--text`, `--due-within N`, `--overdue`,
  `--min-priority`, `--open` (pending work only) and `--history`; `tadu ready`
  lists what can start now; `tadu show KEY` prints one item. When more items
  follow, a list says so on stderr: page with `--offset` or narrow the filter.
- Before recording work or reopening an old task, run `tadu similar "<title>"`
  and update the existing item instead of creating a duplicate.
- Record actionable bugs, risks, blockers, deferred work, missing tests,
  validation, documentation, and product improvements as they are discovered.
- Use `[ ]` pending, `[~]` partial or unverified, `[!]` blocked, `[x]` verified
  complete, `[-]` obsolete or superseded (in format 2: pending, in_progress,
  blocked, done, cancelled). Keep blockers open and name the smallest action
  required to unblock them.
- Format 1: when work becomes `[x]` or `[-]`, remove it from `TODO.md` and add
  a dated entry to `TODO_LOG.md` under `## YYYY` and `### YYYY-MM` headings, in
  the shape below. An `[x]` entry needs an `Evidence:` line and a `[-]` entry a
  `Resolution:` line, each with content.
- Format 1: give an item a `Kind:` field when it is clear what it is: `task`
  for work you can do, `decision` for a choice a person must make, `waiting` for
  something someone else owes, `later` for something not to do now. Leave it
  out when unclear. `Due:` is the deadline, `Check on:` the day to look at the
  item again and `Not before:` the day before which it cannot start.
- Take work with `tadu next`; `tadu inbox` lists what waits on a person and
  `tadu urgent` what is urgent. When only a person can answer a question while
  you work alone, record it (format 1: `tadu add --kind decision`; format 2: a
  task of type `decision`), block the task it holds up (format 1:
  `tadu mark --state blocked --note "<blocker>"`; format 2: add the decision to
  its `blocked_by` with `tadu set`), and go on with the next task.
- Format 2: never edit task files by hand. Use `tadu add` (with category, type
  and priority), `tadu set ID key=value`, `tadu claim ID --as agent:<name>`
  before working on a task, and `tadu close --id ID --evidence "<proof>"`
  (`--resolution`, or `--duplicate-of ID`). Close reports the tasks that no
  longer wait on it; decide for each whether it moves to pending. Every command
  is a dry run until `--write`.
- Before reviewing past conversations, consult the history index and skip
  unchanged records already marked `complete` or `irrelevant`. Update a record
  only after its findings are reconciled; interrupted work stays `partial`.
- Do not interrupt the active task for unrelated non-critical work, and do not
  implement unrelated TODO items unless requested. Immediately report critical
  security, destructive, or data-loss findings. Never put secrets in the
  backlog.

```md
- [x] YYYY-MM-DD — **Category:** What was done.
  - Result: What changed.
  - Evidence: The test, command result, commit or PR that proves it.

- [-] YYYY-MM-DD — **Category:** What was dropped.
  - Resolution: Why it no longer applies, or what replaced it.
```

In format 1, close an item with
`tadu close --match "<text>" --evidence "<proof>" --write` (`--resolution` for
`[-]`, `--result` for the Result line); it moves the item and writes the entry
in this shape. `add`, `mark` and `close` print a diff and write only with
`--write`; a connected `tadu mcp` server offers the same tools. Run
`tadu doctor .` after changing the backlog and before committing. If `tadu` is not
on PATH, install it as https://github.com/syntopica/tadu#install describes, or report that it is
missing. Formats: tadu spec v1,
https://github.com/syntopica/tadu/blob/main/spec/todo-format-v1.md, and v2,
https://github.com/syntopica/tadu/blob/main/spec/todo-format-v2.md. The
tadu-create and tadu-work skills automate these workflows and are optional.
<!-- /tadu:rule -->
