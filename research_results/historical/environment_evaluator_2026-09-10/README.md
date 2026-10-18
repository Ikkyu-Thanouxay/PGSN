# Historical delayed-argument environment evaluator

Exact artifact/source commit: `0b7c9b461cc51a8f1b8f0a0b5fa5cf9340746d40`, verified by resolving both report blobs
and all three implementation-reference blobs before copying. Historical research
lineage: `research/cek-baseline-metrics`; this commit is preserved in that history.

This is the older delayed-argument environment evaluator, with implicit Python
call-stack continuation, **not the current strict-CBV CEK**. Arguments are stored
and evaluated when needed. Its historical Current comparator predates free_bound
pruning; no current optimized-PGSN comparison is implied.

Timings were collected without cProfile; counters were measured separately with
environment metrics disabled during timing. Small cases used 1,000 evaluations
per batch, deep cases 100, with seven batches and reported medians of per-batch
averages. Raw individual timing samples were not retained. These are synthetic
subset results, not full real-document results or proof of semantic equivalence.

`day4_benchmark_output.txt` preserves depth-200 Current **57.522224 ms** and
Environment **1.682803 ms**. `day4_results.md` records a separate pass with
58.769072 ms and 1.552054 ms. Both passes are preserved separately; they have
not been reconciled or pooled. The text output is saved summary output, not raw
individual samples. The report also preserves separately measured counters.

Historical implementation provenance (links resolve at the exact commit):

- [experiments/cek_machine/benchmark_pgsn_env_eval.py](https://github.com/Ikkyu-Thanouxay/PGSN/blob/0b7c9b461cc51a8f1b8f0a0b5fa5cf9340746d40/experiments/cek_machine/benchmark_pgsn_env_eval.py) — blob `b47f8cc1d715007cbfe7789eeaf9ff94f6f80a72` (historical source only; not copied).
- [experiments/cek_machine/pgsn_env_eval.py](https://github.com/Ikkyu-Thanouxay/PGSN/blob/0b7c9b461cc51a8f1b8f0a0b5fa5cf9340746d40/experiments/cek_machine/pgsn_env_eval.py) — blob `26577ff6f60c721079f97980cc52a4139265706e` (historical source only; not copied).
- [experiments/cek_machine/test_pgsn_env_eval.py](https://github.com/Ikkyu-Thanouxay/PGSN/blob/0b7c9b461cc51a8f1b8f0a0b5fa5cf9340746d40/experiments/cek_machine/test_pgsn_env_eval.py) — blob `5f13487e929c669b78ca1ddd03990b4fd13d2e10` (historical source only; not copied).

| Archived file | Original path at source commit | Source blob SHA | Copy blob SHA |
|---|---|---|---|
| [experiments/cek_machine/day4_results.md](experiments/cek_machine/day4_results.md) | experiments/cek_machine/day4_results.md | 2a7a1d7f666832075abf7ceb2486080818cd7ef0 | 2a7a1d7f666832075abf7ceb2486080818cd7ef0 |
| [experiments/cek_machine/day4_benchmark_output.txt](experiments/cek_machine/day4_benchmark_output.txt) | experiments/cek_machine/day4_benchmark_output.txt | 948129f967c9874397969c9e6a9fc74a89750daf | 948129f967c9874397969c9e6a9fc74a89750daf |
