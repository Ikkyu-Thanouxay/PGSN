# Full cold traced-memory experiment

The separate full coordinator leaves the committed pilot harness and worker unchanged.
Run only after committing and checking the implementation; the coordinator requires
a completely clean working tree and refuses every existing output directory.

```sh
.venv/bin/python -B experiments/cek_machine/benchmark_memory_full.py --full --output research_results/cek/memory/<unique-run-id>
.venv/bin/python -B experiments/cek_machine/benchmark_memory_full.py --verify-only --output research_results/cek/memory/<existing-run-id>
```

Identity and Captured, n=10,100,200, ten repetitions: 120 evaluator observations plus
60 separately recorded no-evaluation controls. Each observation launches the same
unchanged worker in a new Python interpreter and constructs a fresh input. No
warmups, pre-evaluation, profiling counters, execution-time samples, or RSS.
Current/CEK order alternates per repetition; controls are last in each repetition.
All measurement, GC, retained-reference, nameless-input and caching policies are
unchanged from [the pilot](MEMORY.md). Cold means first evaluator call, not a cold
interpreter or OS. The complete fully_eval/evaluate calls remain inside the boundary.

Raw per-observation JSON is retained immediately, then combined JSON/CSV plus a
separate error inventory. Integer byte fields are baseline, absolute peak, ending,
peak growth and end growth. Peak growth is net peak above baseline, not cumulative
allocation volume or total process memory. Do not automatically subtract controls.
The 60-second worker timeout is a safety limit, not an execution-time measurement.

Metadata records exact Git commit, hashes of implementation/production sources and
all earlier evidence, worker Python/platform/GC details, command, ordering and units.
The saved-data verifier checks coverage, isolation/PIDs, correctness, arithmetic,
JSON/CSV agreement, errors, source hashes, and unchanged earlier evidence.

After measurement, use analyze_memory_full.py in a separate environment with
Matplotlib (this dependency is not needed in measurement workers):

```sh
/path/to/plot-python -B experiments/cek_machine/analyze_memory_full.py --output research_results/cek/memory/<existing-run-id>
.venv/bin/python -B experiments/cek_machine/analyze_memory_full.py --verify-only --output research_results/cek/memory/<existing-run-id>
```

Analysis refuses existing output artifacts. Summary CSV records median, inclusive
quartiles, IQR, minimum and maximum for all five metrics per condition, with errors
counted separately. PNG/SVG graphs show peak growth in KiB against numeric n,
Current blue and CEK green, with IQR bars and separate gray controls. Report,
analysis environment, plot version and artifact hashes are retained in the run.
No outliers are removed. Six configurations on one machine/session do not establish
general memory superiority, mathematical complexity, or production-wide behavior.
