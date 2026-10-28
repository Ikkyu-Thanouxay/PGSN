# PGSN evaluator performance research

The research asks where PGSN evaluation spends time, how earlier optimizations
changed its work, and how an experimental CEK evaluator compares on supported
programs. CEK evaluates terms using explicit environments and a continuation
(the remaining work), rather than repeatedly rewriting the whole term.

Read the experiments in date order below. “Current” in an old report means the
PGSN version measured then, not today's code. [manifest.csv](manifest.csv)
records exact checkpoints, timing boundaries, sample retention and limitations.
[Branch provenance](branch_provenance.md) explains the preserved Git history.

## Experiment history

| Date / experiment | Purpose and source | Raw evidence and summaries | Report / main finding and limit |
|---|---|---|---|
| 2026-06-25 profiling reference | Early profiling; exact source/setup unknown | [Retained reference](historical/pre_free_bound_2026-07-19/reports/profiler/2026-06-25/README.md); ten referenced raw files are missing | [Archive explanation](historical/pre_free_bound_2026-07-19/README.md); no reconstructed measurements |
| 2026-07-19 historical profiling | Identify rewriting costs before free-variable-bound pruning; [source checkpoint](https://github.com/Ikkyu-Thanouxay/PGSN/tree/83e932ca0f1fd76ef2f9b85b1550fe783f72ff9c) | [Five raw profiles](historical/pre_free_bound_2026-07-19/reports/profiler/2026-07-19/raw/), [before/after outputs](historical/pre_free_bound_2026-07-19/reports/profiler/2026-07-19/baseline_outputs/), [summary](historical/pre_free_bound_2026-07-19/study/cek_machine/baseline_metrics.md) | [Archive report](historical/pre_free_bound_2026-07-19/README.md); repeated traversal counts retained; profiler plus counters distort elapsed times |
| 2026-09-10 environment experiment | Explore delayed arguments; [historical scripts and exact source links](historical/environment_evaluator_2026-09-10/README.md) | [Saved benchmark summary](historical/environment_evaluator_2026-09-10/experiments/cek_machine/day4_benchmark_output.txt); individual timing samples not retained | [Separate report pass](historical/environment_evaluator_2026-09-10/experiments/cek_machine/day4_results.md); synthetic cases only; this evaluator is not strict CBV |
| 2026-09-22 M2 basic comparison | Compare optimized PGSN with strict call-by-value (CBV) CEK; [benchmark](../experiments/cek_machine/benchmark.py), [machine](../experiments/cek_machine/cbv_cek.py), [counters](../experiments/cek_machine/metrics.py) | Medians/counters in report; original 11-run samples not retained | [M2 report](../docs/cbv_cek_milestone2_results.md); supports comparison on shared scalar cases; SolarWinds 0.616 s is PGSN-only context |
| 2026-09-29 M3 recursion | Study recursive scaling; [benchmark](../experiments/cek_machine/benchmark_recursion.py) | Original summaries in report; original 11-run samples not retained | [M3 report](../docs/cbv_cek_milestone3_results.md); input preparation failed at n=200, so no timing there |
| 2026-10-11 recursion validation | Check scaling with more repetitions; [benchmark](../experiments/cek_machine/benchmark_recursion.py), [analysis](../experiments/cek_machine/analyze_recursion_validation.py) | [CSV: raw arrays, statistics, counters](cek/recursion_validation/2026-10-11/cbv_cek_milestone3_validation.csv) | [Validation report](../docs/cbv_cek_milestone3_validation.md); approximately linear over n=0–150, with 500 samples per evaluator/size; one workload/session |
| 2026-10-14 basic validation | Check small-case timings with more repetitions; [script](../experiments/cek_machine/benchmark_basic_validation.py) | [Nine raw CSVs](cek/basic_validation/2026-10-14/raw/), [summary](cek/basic_validation/2026-10-14/summary.csv), [metadata](cek/basic_validation/2026-10-14/metadata.json) | [Original run report](cek/basic_validation/2026-10-14/README.md); 500 paired samples per case; fixed PGSN-first order and warm execution |
| 2026-10-19 current PGSN examples | Measure real inputs in fresh processes; [harness](../experiments/performance/README.md), [coordinator](../experiments/performance/current_pgsn_benchmark.py), [worker](../experiments/performance/current_pgsn_worker.py) | [Raw samples](current_pgsn/runs/2026-10-19_current_pgsn_examples/raw_samples.json), [summary](current_pgsn/runs/2026-10-19_current_pgsn_examples/summary.csv), [metadata](current_pgsn/runs/2026-10-19_current_pgsn_examples/metadata.json), [profiles](current_pgsn/runs/2026-10-19_current_pgsn_examples/profiles/), [counters](current_pgsn/runs/2026-10-19_current_pgsn_examples/counters.json) | [Run report](current_pgsn/runs/2026-10-19_current_pgsn_examples/README.md); 24 XML and four Python inputs successfully measured; no full-program CEK comparison |

## What the evidence supports

- Current PGSN retains 1,142 measured clean samples and 115 warmups, plus 29
  pilots. All 53 inputs have metadata/status. SolarWinds XML evaluation median
  is 0.617027 s in this run; full EU AI Act wrappers take much longer.
- Basic validation retains 500 paired samples for each of nine cases. Recursion
  validation retains 500 samples per evaluator at each of 16 sizes. Saved-data
  checks confirm the basic summary statistics and recursion medians.
- Historical output pairs preserve agreement for four inputs. Identical bytes
  in each before/after pair are evidence, not unwanted duplicates.
- Clean timings, operation counters, and profiler diagnostics have different
  purposes. Do not combine instrumented historical times with clean timings
  to claim a controlled speedup. [Implementation documentation](../PGSN-implementation.md)
  contains further historical figures with incomplete measurement setup.

These are local measurements, not proof of universal speedups or semantic
agreement. Strict CBV differs from production rewriting semantics. Original
M2/M3 and September timing series are unavailable; June raw profiles are
missing. Current-PGSN metadata records a clock discrepancy, a package-version
label mismatch, and a Python SolarWinds conversion error. See individual reports.
No saved performance plot or plot-generation script accompanies these datasets;
the recursion report explains that the earlier slide/plot is absent.

## Reproduction and future results

Use [current reproduction and verification commands](path_migration.md), not
historical output paths embedded in immutable run files. Never overwrite an
existing run. Keep code/tests in `experiments/`, milestone reports and plans in
`docs/`, and new evidence in a fresh dated run directory:

- `research_results/current_pgsn/runs/<unique-run-id>/`
- `research_results/cek/basic_validation/<unique-run-id>/`
- `research_results/cek/recursion_validation/<unique-run-id>/`

Retain raw samples, metadata, exact source commit, command, environment, timing
units/boundaries, statuses, summary and any generated plots together. Link each
new run here and in the manifest. Preserve the historical archive unchanged.

[examples.csv](examples.csv) inventories 24 PGSN XML programs, 17 XML modules
and 12 Python files. Modules are not standalone benchmarks; static eligibility
is not a guarantee of import safety or successful evaluation. Counterpart
filenames alone do not establish XML/Python output equality.

See also the [CEK index](cek/README.md), [research plan](../docs/cbv_cek_research_plan.md),
[research log](../docs/research_log.md), [midterm support](midterm_abstract_support_2026-10-19.md),
and [evidence hash ledger](evidence_hashes_sha256.csv).
