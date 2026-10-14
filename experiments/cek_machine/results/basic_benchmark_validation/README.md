# Basic CBV CEK benchmark validation

The professor requested more repetitions because the original millisecond-scale
benchmark used only 3 warm-ups and 11 measured runs. This re-measurement uses
20 warm-up evaluations and 500 measured evaluations per evaluator for each of
the nine identity, captured, and arithmetic cases at n = 10, 100, 200.
Medians remain the intended main paper statistic.

Workload semantics and evaluator behavior were not changed. The script imports
the original workload builders and timing helpers from benchmark.py. Terms are
constructed once per case before timing. Expected results are checked with both
evaluators before timing, on every warm-up and measured evaluation, and after
timing. Existing instrumented metrics run outside timing. Current runs first,
then CEK, in every iteration; perf_counter and the original timing boundaries
are preserved. No recursion limit or garbage collection setting is changed.

raw/ contains all paired samples in milliseconds (run,current_ms,cek_ms).
summary.csv contains statistics and existing evaluator counters. Quartiles use
inclusive linear interpolation; standard deviation uses the sample definition
(n-1). Raw floats are saved without decimal rounding. metadata.json records the
environment, source commit, command, and UTC run times. An error aborts the run;
partial output is retained and existing output directories are never overwritten.

Reproduce from the repository root with a fresh output directory:

```sh
python experiments/cek_machine/benchmark_basic_validation.py --warmups 20 --runs 500 --sizes 10 100 200 --output experiments/cek_machine/results/basic_benchmark_validation
```

Verify saved statistics without re-measuring:

```sh
python experiments/cek_machine/benchmark_basic_validation.py --verify-only --runs 500 --sizes 10 100 200
```
