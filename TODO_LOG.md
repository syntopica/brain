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
