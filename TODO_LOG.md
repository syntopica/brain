# Closed work

<!-- tadu:log v1 since 2026-10-12 -->

## 2026

### October

- 2026-10-11 [x] **`brain graph --json --no-html` p95 at the 2 s polling
  budget.** The gap was not only the second interpreter: `brain_cli` loaded and
  validated the configuration (about 20 git processes for the root and remote
  checks) and then `graph/build.py` did it again. The dispatcher now leaves the
  load to `index`, `graph` and `find`, and runs `graph` in-process. Measured
  interleaved in one session under load average 36-179, 20 runs each against
  the full instance: before p95 1.53 s / 1.21 s, after 1.24 s / 0.56 s, `graph.py`
  directly 1.04 s / 0.70 s; output byte-identical to `graph.py`. Evidence:
  `bin/brain --data <instance> graph --json --no-html` timed against
  `tools/graph/build.py`; `uv run codeality-py gate` green.

- 2026-10-11 [x] **`tools/eval/run.py` read `SYNTOPICA_DATA` as the pages
  root.** It now selects the instance like every other command (`--data`, then
  `SYNTOPICA_DATA`, then the upward walk) and scores the configured page
  directories under the index's directory, as `brain find` does. With
  `SYNTOPICA_DATA` at the instance root and the private query set: 23
  questions, keyword 0.91, pagerank 0.91 (was 0.09 for both). Tests:
  `tests/test_eval_baselines.py` builds a synthetic instance and covers the
  environment path and the missing-instance error.

### 2026-10

- [x] 2026-10-22 — **Doctor Git inspection timeout classification:** Distinguish operational Git deadlines from invalid repository settings.
  - Result: Report a sanitized git_inspection_timeout code for configuration, repository recheck and archive deadlines. Preserve the five-second deadline, fail-closed repository validation and ordinary invalid-identity codes. Configured-instance health still needs its own live check.
  - Evidence: Eight focused synthetic and invalid-schema checks passed after reproducing the repository-recheck misclassification. The source-matched isolated doctor subset passed all fourteen tests. In the exact locked wheel-only environment, python -m pytest -q passed 636 tests with five existing skips, and codeality-py gate --json passed all seven required stages. Independent review found no remaining issues. Initial Git-root and missing-uv verification setup failures were retained and corrected without changing assertions or timeouts.

- [x] 2026-10-22 — **Dependency security:** Update the locked certificate trust bundle.
  - Result: Update only the certifi package record from 2026.7.22 to 2026.10.19, addressing GHSA-6q48-6c7w-9gw2 and PYSEC-2026-4320. Preserve all other package records, sources, lock metadata and policy. Installed instances require separate verification.
  - Evidence: Structural TOML comparison found exactly one changed package record and no added or removed packages. The official wheel SHA256 is 42d35340cc5b9ba78e818ddbff0c5b1c2b779de448a340fd1b989f5fa8670e1b. The source-matched locked environment passed python -m pytest -q (636 passed, five existing skips) and codeality-py gate --json (all seven required stages); pip-audit checked 45 distributions with zero vulnerabilities and no waivers.
