# Open work

- [ ] **`brain graph --json --no-html` p95 is at the 2 s polling budget.**
  Measured 2026-10-03 on the full instance under load average 29-53: p95
  1.96 s and 2.15 s over two sets of 10 runs, max RSS 28 MB, CPU under 0.8 s
  per run; `graph.py` called directly took p95 0.73 s, so the `brain` wrapper's
  second Python process is most of the gap. Smallest step: re-measure on a
  quiet machine; if it still misses, run `graph` in-process in `brain_cli.py`.

- [ ] **`tools/eval/run.py` reads `SYNTOPICA_DATA` as the pages root, not the
  instance root.** Measured 2026-09-25 with the private set at
  `~/p/wiki/tools/eval/queries.toml`: `SYNTOPICA_DATA=~/p/wiki` (what the drip
  and the engine take) scores recall@5 0.09 for both baselines because
  `load_pages` finds no `projects/`, `business/`, ... under it and only the
  refusal cases score; `SYNTOPICA_DATA=~/p/wiki/brain` scores keyword 0.91 and
  pagerank 0.87. Smallest step: resolve the pages root in `run.py` the way
  `brain find` does, so one `SYNTOPICA_DATA` value serves every command.

