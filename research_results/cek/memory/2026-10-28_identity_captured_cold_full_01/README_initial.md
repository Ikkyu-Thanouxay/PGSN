# Full cold traced-memory experiment

This run measures traced live Python blocks, not total process memory, RSS, or cumulative allocation volume.

Source commit: `4f3a6319091a9225632689aa585a8950c7b08f93`. Clean implementation at launch; exact source and earlier-evidence hashes are in [metadata.json](metadata.json).

Command: `/Users/fakedev/PGSN_Workspace/dev_library/PGSN/.venv/bin/python -B experiments/cek_machine/benchmark_memory_full.py --full --output research_results/cek/memory/2026-10-28_identity_captured_cold_full_01`.

Worker environment: [('3.14.7 (main, Aug  5 2026, 10:29:49) [Clang 21.0.0 (clang-2100.1.1.101)]', 'macOS-26.5.2-arm64-arm-64bit-Mach-O')].

Identity and Captured at n=10,100,200; 10 observations per evaluator/size (120), plus 10 separate controls per family/size (60).
Each observation executes a fresh interpreter with a freshly built nameless term; Current/CEK order alternates by repetition.
No evaluator warmups, timing measurements, RSS, or counter instrumentation. Automatic GC stays enabled, with one explicit collection before baseline.
The unchanged pilot worker measures complete fully_eval(steps=10000) or complete CEK evaluate(), including initial-state creation and loop.
Tracing starts before construction with one traceback frame. Input/expected/result are retained through the final measurement; correctness is checked afterward.

Raw B (baseline), P (absolute peak), E (ending), P-B (peak growth), and E-B (end growth) are retained in bytes.
Baseline includes prepared inputs; cold means first evaluator call, not a cold interpreter or cold OS cache.

| Input | n | Current median / IQR / min–max (bytes) | CEK median / IQR / min–max (bytes) | Control median (bytes) |
|---|---:|---:|---:|---:|
| identity | 10 | 3600 / 0 / 3600–3600 | 6720 / 0 / 6720–6720 | 176 |
| identity | 100 | 7576 / 0 / 7576–7576 | 25112 / 0 / 25112–25112 | 176 |
| identity | 200 | 7576 / 0 / 7576–7576 | 42712 / 0 / 42712–42712 | 176 |
| captured | 10 | 8304 / 0 / 8304–8304 | 9112 / 0 / 9112–9112 | 176 |
| captured | 100 | 16976 / 0 / 16976–16976 | 36336 / 0 / 36336–36336 | 176 |
| captured | 200 | 17008 / 0 / 17008–17008 | 63536 / 0 / 63536–63536 | 176 |

All five memory metrics have median, inclusive q1/q3, IQR, min and max in [summary.csv](summary.csv). No outliers were removed.
Correctness/coverage: `{"status": "passed", "observations": 180, "evaluator_observations": 120, "controls": 60, "correct_evaluations": 120, "errors": 0, "unique_successful_worker_pids": 180, "units": "bytes"}`. Errors are separately retained in [errors.json](errors.json).

Graph: [PNG](peak_growth.png), [SVG](peak_growth.svg). Blue = Current PGSN; green = CEK. Numeric input-size axis; IQR bars.

These results describe two shared synthetic workloads on one machine/session. Tracing and measurement bookkeeping have overhead.
Controls are shown separately and not subtracted. End growth alone is not evidence of a leak. Zero IQR does not prove zero uncertainty.
Do not infer general evaluator memory superiority or asymptotic complexity from these six configurations.

Verify raw data with benchmark_memory_full.py --verify-only --output this-directory.
Verify summaries/artifact hashes with analyze_memory_full.py --verify-only --output this-directory.
Earlier evidence preservation is checked against all hashes captured at launch.
