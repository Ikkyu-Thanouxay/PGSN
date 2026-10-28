"""Re-measure the existing basic benchmark without changing its semantics."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shlex
import statistics
import subprocess
import sys
import time

from benchmark import (identity, captured, arithmetic, evaluate, measure_current,
                       measure_cek, time_current, time_cek)

FAMILIES = [('identity', identity), ('captured', captured), ('arithmetic', arithmetic)]
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / 'research_results/cek/basic_validation/2026-10-14'


def check(result, expected):
    if result != expected:
        raise AssertionError(f'Evaluator result {result!r} differs from {expected!r}')


def prepare(build, size):
    # Construction and instrumented metrics are outside every timed evaluation.
    term, expected = build(size)
    check(term.fully_eval(steps=10000), expected)
    check(evaluate(term), expected)
    current_result, current = measure_current(term)
    cek_result, cek = measure_cek(term)
    check(current_result, expected)
    check(cek_result, expected)
    counters = {f'current_{key}': value for key, value in asdict(current).items()}
    counters.update({f'cek_{key}': value for key, value in asdict(cek).items()
                     if not key.endswith('_seconds')})
    return term, expected, counters


def stats(values, prefix):
    # Explicit inclusive linear-interpolation quartiles, sample standard deviation.
    q1, _, q3 = statistics.quantiles(values, n=4, method='inclusive')
    return {f'{prefix}_{key}_ms': value for key, value in dict(
        median=statistics.median(values), mean=statistics.mean(values),
        stdev=statistics.stdev(values), q1=q1, q3=q3, iqr=q3-q1,
        min=min(values), max=max(values)).items()}


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_saved(output, sizes, runs):
    """Independently load saved samples and reproduce every summary statistic."""
    with (output / 'summary.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    expected_cases = {(name, str(size)) for name, _ in FAMILIES for size in sizes}
    if len(rows) != len(expected_cases) or {(r['family'], r['size']) for r in rows} != expected_cases:
        raise AssertionError('Unexpected summary cases')
    for row in rows:
        if row['status'] != 'ok' or int(row['sample_count']) != runs:
            raise AssertionError('Unsuccessful case or incorrect sample count')
        path = output / 'raw' / f"{row['family']}_n{row['size']}.csv"
        with path.open(newline='') as stream:
            samples = list(csv.DictReader(stream))
        if len(samples) != runs or [int(s['run']) for s in samples] != list(range(1, runs+1)):
            raise AssertionError(f'Incorrect samples in {path}')
        for prefix in ('current', 'cek'):
            values = [float(s[f'{prefix}_ms']) for s in samples]
            if not all(value > 0 for value in values):
                raise AssertionError(f'Nonpositive timing in {path}')
            for key, value in stats(values, prefix).items():
                if float(row[key]) != value:
                    raise AssertionError(f'Summary mismatch: {path}: {key}')
    print(f'Verified {len(rows)} cases, {runs} samples per evaluator per case, all saved statistics match.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--warmups', type=int, default=20)
    parser.add_argument('--runs', type=int, default=500)
    parser.add_argument('--sizes', type=int, nargs='+', default=[10, 100, 200])
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--check-only', action='store_true', help='Verify results and metrics without timing or writing files')
    parser.add_argument('--verify-only', action='store_true', help='Recompute saved summaries from raw samples')
    args = parser.parse_args()
    if args.warmups < 0 or args.runs < 2 or len(set(args.sizes)) != len(args.sizes):
        parser.error('Require nonnegative warmups, at least two runs, and unique sizes')
    if args.verify_only:
        verify_saved(args.output, args.sizes, args.runs)
        return
    if args.check_only:
        for name, build in FAMILIES:
            for size in args.sizes:
                prepare(build, size)
                print(f'{name} n={size}: correctness and metrics ok', flush=True)
        return
    # Refuse to overwrite data from any previous or partial run.
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'raw').mkdir()
    root = Path(__file__).resolve().parents[2]
    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=root, text=True).strip()
    metadata = dict(branch=git('branch', '--show-current'), starting_commit_sha=git('rev-parse', 'HEAD'),
                    python_version=sys.version, python_executable=sys.executable,
                    platform=platform.platform(), machine=platform.machine(),
                    warmups=args.warmups, measured_runs=args.runs, sizes=args.sizes,
                    workloads=[name for name, _ in FAMILIES], timing_function='time.perf_counter',
                    clock_info=vars(time.get_clock_info('perf_counter')),
                    construction_outside_timing=True, metrics_outside_timing=True,
                    evaluation_order='Current then CEK in every warmup and measured iteration',
                    cek_timing='Existing time_cek total, including initial_state and its intermediate perf_counter call',
                    quartile_method='statistics.quantiles(n=4, method="inclusive")',
                    stdev_method='statistics.stdev (sample standard deviation, n-1)',
                    command=shlex.join(['python', *sys.argv]), cwd=str(Path.cwd()),
                    started_at_utc=datetime.now(timezone.utc).isoformat(), status='running')
    metadata_path = args.output / 'metadata.json'
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n')
    rows = []
    for name, build in FAMILIES:
        for size in args.sizes:
            term, expected, counters = prepare(build, size)
            for _ in range(args.warmups):
                check(time_current(term)[0], expected)
                check(time_cek(term)[0], expected)
            samples = []
            for run in range(1, args.runs+1):
                result, duration = time_current(term)
                check(result, expected)
                result, total, _, _ = time_cek(term)
                check(result, expected)
                samples.append(dict(run=run, current_ms=duration*1000, cek_ms=total*1000))
            # Also recheck both evaluators after timing.
            check(term.fully_eval(steps=10000), expected)
            check(evaluate(term), expected)
            write_csv(args.output / 'raw' / f'{name}_n{size}.csv', samples)
            row = dict(family=name, size=size, status='ok', sample_count=len(samples))
            for prefix in ('current', 'cek'):
                row.update(stats([s[f'{prefix}_ms'] for s in samples], prefix))
            row.update(counters)
            rows.append(row)
            print(f"{name} n={size}: ok; Current {row['current_median_ms']:.6f} ms; CEK {row['cek_median_ms']:.6f} ms", flush=True)
    write_csv(args.output / 'summary.csv', rows)
    verify_saved(args.output, args.sizes, args.runs)
    metadata.update(status='ok', completed_at_utc=datetime.now(timezone.utc).isoformat(),
                    all_evaluation_results_checked=True, raw_summary_verification='passed')
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n')
    (args.output / 'README.md').write_text('''# Basic CBV CEK benchmark validation

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
python experiments/cek_machine/benchmark_basic_validation.py --warmups 20 --runs 500 --sizes 10 100 200 --output research_results/cek/basic_validation/<unique-run-id>
```

Verify saved statistics without re-measuring:

```sh
python experiments/cek_machine/benchmark_basic_validation.py --verify-only --runs 500 --sizes 10 100 200 --output research_results/cek/basic_validation/<unique-run-id>
```
''')


if __name__ == '__main__':
    main()
