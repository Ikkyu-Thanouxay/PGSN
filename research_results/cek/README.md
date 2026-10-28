# Current PGSN versus strict-CBV CEK evidence

Saved CEK datasets are stored below this index. See [migration notes](../path_migration.md) for original paths and current reproduction commands.

Basic benchmark validation: [README](basic_validation/2026-10-14/README.md),
[metadata.json](basic_validation/2026-10-14/metadata.json),
[summary.csv](basic_validation/2026-10-14/summary.csv),
and [raw directory](basic_validation/2026-10-14/raw/).
The nine raw CSVs contain 500 paired timing samples each (Current and CEK),
for identity/captured/arithmetic at n=10,100,200; 20 warm-ups precede each case.
Summary CSV contains statistics/counters; metadata records timing scope and environment.

Recursion validation: [CSV](recursion_validation/2026-10-11/cbv_cek_milestone3_validation.csv),
[report](../../docs/cbv_cek_milestone3_validation.md),
[analysis script](../../experiments/cek_machine/analyze_recursion_validation.py),
[benchmark definition](../../experiments/cek_machine/benchmark_recursion.py).
The CSV retains 500 raw samples per evaluator per size in JSON-array fields,
as well as derived statistics and counters, for 16 sizes from 0 to 150.

[Milestone 2](../../docs/cbv_cek_milestone2_results.md) and
[Milestone 3](../../docs/cbv_cek_milestone3_results.md) are historical milestone
summaries using optimized Current PGSN. Their original 3-warmup/11-run individual
samples were not retained. The M2 SolarWinds optimized context timing is Current
only, not a CEK comparison.

These controlled comparisons use current optimized rewriting PGSN (cached
free_bound pruning) versus experimental strict-CBV CEK on supported synthetic
terms. Timings exclude construction/name preparation; counters run separately,
without cProfile in measured timings. Current and strict CBV have semantic
boundaries; consult the reports. No full SolarWinds or EU AI Act CEK comparison
exists yet. No benchmark or analysis script was executed during consolidation.
