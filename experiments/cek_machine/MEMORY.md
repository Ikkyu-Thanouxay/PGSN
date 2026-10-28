# Traced-memory pilot

This prototype reuses the existing Identity/Captured builders and evaluators.
The coordinator intentionally supports only a three-observation pilot, not the
full experiment. Run from the repository root in the existing environment:

```sh
.venv/bin/python -B experiments/cek_machine/benchmark_memory.py --pilot --output research_results/cek/memory/<unique-run-id>
.venv/bin/python -B experiments/cek_machine/benchmark_memory.py --verify-only --output research_results/cek/memory/<existing-run-id>
```

Replace angle-bracket placeholders with real run names. Existing output directories
are refused before any workers start. JSON files use exclusive creation. Each of
Current, CEK and the control runs in its own fresh interpreter, on Identity n=10.
The worker also supports tiny Captured inputs for focused tests. No warmups,
pre-evaluation, timing results, counter wrappers, cProfile, or RSS are collected.

Imports finish before tracing. tracemalloc starts with one traceback frame before
input construction. Inputs are nameless, so actual remove_name conversion is not
performed. After one explicit GC collection, automatic GC remains enabled.
Baseline B is read immediately before resetting the peak and executing one call.
Current uses complete fully_eval(steps=10000); CEK uses its unchanged evaluate(),
which includes initial_state and its transition loop. Input and expected result
remain referenced. Result remains alive through the ending/peak read. Tracing
then stops, and correctness is checked. No snapshots or serialization occur inside
the measured call. Measurement reads/local variables still add small overhead.
The no-evaluation control uses the same builder and returns the original input;
it is marked not evaluated, not incorrectly presented as a successful evaluation.

All values are integer bytes:

- B: traced live memory after preparation, including retained input/expected.
- P: absolute peak traced live memory during the evaluation boundary.
- E: traced live memory at the ending read with the result retained.
- P-B: maximum net growth over the prepared baseline, not cumulative allocations.
- E-B: net memory change at completion; this may be negative in general.

These are traced Python blocks, not total RAM/RSS, process peak, all native
allocations, or total allocations over time. Tracer bookkeeping has overhead.
Do not subtract the control automatically or infer general superiority from a
single observation. This is first evaluation with unprimed syntax caches, unlike
older warm timing measurements. Errors and failed validation are retained; the
coordinator exits nonzero on invalid data. A worker timeout is 60 seconds.

Metadata records Git base and dirty status, commands, harness/evaluator source
SHA-256 hashes, measurement policy, and units. Worker JSON includes Python,
platform, GC policy, recursion limit, PID and errors. CSV is a compact projection.
No summaries implying replication are generated for this pilot. Keep future full
runs in new directories under research_results/cek/memory/ and write their report
under docs/ only after agreeing on the next experiment.
