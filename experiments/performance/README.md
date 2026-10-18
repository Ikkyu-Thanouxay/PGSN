# Current-PGSN real-program research harness

`current_pgsn_benchmark.py` coordinates sequential, fresh-process workers and
validates saved results. `current_pgsn_worker.py` owns the measurement pipeline
and separate counter/profile modes. Tests use fast fixtures and static source
inspection; they do not evaluate the four slow EU wrappers.

Run only from a clean committed source tree, with a new output directory:

```sh
.venv/bin/python experiments/performance/current_pgsn_benchmark.py --output research_results/current_pgsn/runs/<unique-run-id>
```

Each pilot, warmup, measured sample, counter pass and cProfile pass has its own
Python subprocess, with default GC enabled and the unchanged recursion limit.
A warmup warms OS/system caches; it does not preserve evaluator caches across
workers. No outliers are removed. All pilots finish and their repetition
selections are saved before main measurements. Fixed policy uses pilot worker
pipeline duration: <0.1s 5/50, <1s 3/20, <10s 2/10, <60s 1/5, otherwise 0/3
(warmups/measured). Every successful measurement has its own total sample;
summary totals are never sums of phase medians. Inclusive quartiles and sample
standard deviation are used. Default clean timeout is 1,800s per worker;
diagnostic timeout is 3,600s. Errors/timeouts remain explicit statuses.

Load timing includes initial PGSN imports, XML compilation or explicit Python
module execution/Term construction. XML uses `compile_pgsn`, because `load_xml`
also evaluates. Fully-eval timing uses production `fully_eval(steps=1000000)`:
initial name removal is inside this API timing when the term is named.
GSN conversion uses `gsn_tree` on the evaluated result; current `python_value`
calls `to_python` without reevaluating. Output uses `Tree.show(stdout=False,
sorting=False, idhidden=True, line_type='ascii-ex')` and UTF-8 SHA-256 outside
evaluation timing. Random internal UUID identifiers are hidden. The hash is
repeatability evidence, not an independent semantic specification.

`worker_total_seconds` measures the pipeline from before PGSN/input loading
through conversion, output and hashing. It excludes interpreter startup,
worker standard-library imports, environment metadata extraction and JSON
transport. `process_wall_seconds` includes startup, all imports, metadata and
JSON transport/process completion. Each timing has raw samples and its own
statistics. Workers capture unexpected program stdout as an error.

All 53 static registry entries appear in sources and summary. XML modules have
metadata only. Transitive local XML imports are parsed statically, deduplicated,
hashed and counted; missing/jailed imports are listed as unresolved. Comments
are not imports. Python entries are an explicit five-file allowlist, inspected
without importing the other seven files. SolarWinds.py appends to sys.path at
import; the effect is confined to its isolated worker. No original example is
rewritten. Corresponding XML/Python output equality is never assumed.

Counters reproduce CEK research definitions: successful outer progressions,
lambda-head Context reductions, public shift/subst method entries (including
recursive/pruned entries), and free_bound early exits. Initial name removal is
outside counter wrappers, as in CEK metrics. The outer loop mirrors fully_eval;
wrappers are restored in finally. Counter elapsed fields are explicitly diagnostic.
cProfile runs only fully_eval after loading, including API name removal, with
no counters. Profile reports retain call counts and top cumulative/self-time
functions; recursive cumulative times are not additive phase costs.

CSV files are analysis-friendly projections. JSON raw files also retain each
worker's environment and exact floating-point values; no individual sample is
discarded. `--verify-only --output <existing-run>` recomputes statistics, policy,
raw counts, hashes, dependency hashes and diagnostic-mode separation without
running evaluations. Results must validate before a results commit.
