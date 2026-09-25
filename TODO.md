# Open work

- [ ] **`tools/eval/run.py` reads `SYNTOPICA_DATA` as the pages root, not the
  instance root.** Measured 2026-09-25 with the private set at
  `~/p/wiki/tools/eval/queries.toml`: `SYNTOPICA_DATA=~/p/wiki` (what the drip
  and the engine take) scores recall@5 0.09 for both baselines because
  `load_pages` finds no `projects/`, `business/`, ... under it and only the
  refusal cases score; `SYNTOPICA_DATA=~/p/wiki/brain` scores keyword 0.91 and
  pagerank 0.87. Smallest step: resolve the pages root in `run.py` the way
  `brain find` does, so one `SYNTOPICA_DATA` value serves every command.

