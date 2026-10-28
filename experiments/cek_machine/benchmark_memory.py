"""Pilot-only coordinator and saved-data verifier for traced Python memory."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = ROOT / 'research_results/cek/memory'
MODES = ('current', 'cek', 'control')
FIELDS = ('family', 'size', 'evaluator', 'pid', 'status', 'correct', 'evaluated',
          'baseline_bytes', 'peak_bytes', 'ending_bytes', 'peak_growth_bytes', 'end_growth_bytes')
SOURCES = ('experiments/cek_machine/benchmark_memory.py',
           'experiments/cek_machine/memory_worker.py', 'experiments/cek_machine/benchmark.py',
           'experiments/cek_machine/cbv_cek.py', 'src/pgsn/pgsn_term.py')


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def run_worker(mode):
    command = [sys.executable, '-B', str(Path(__file__).with_name('memory_worker.py')),
               '--family', 'identity', '--size', '10', '--evaluator', mode]
    try:
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        row = json.loads(process.stdout)
        row.update(command=command, returncode=process.returncode, stderr=process.stderr)
        if process.returncode or process.stderr:
            row['status'] = 'worker_error'
        return row
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as error:
        return dict(family='identity', size=10, evaluator=mode, status='worker_error',
                    error_type=type(error).__name__, error=str(error), command=command)


def verify(directory):
    rows = json.loads((directory / 'raw_samples.json').read_text())
    meta = json.loads((directory / 'metadata.json').read_text())
    if len(rows) != 3 or [r['evaluator'] for r in rows] != list(MODES):
        raise ValueError('Expected exactly the three pilot observations')
    if len({r['pid'] for r in rows}) != 3:
        raise ValueError('Observations were not isolated')
    for row in rows:
        if row['status'] != 'ok' or row['family'] != 'identity' or row['size'] != 10:
            raise ValueError('Failed or unexpected pilot observation')
        b, p, e = (row[k] for k in ('baseline_bytes', 'peak_bytes', 'ending_bytes'))
        if not all(type(v) is int and v >= 0 for v in (b, p, e)):
            raise ValueError('Invalid memory units/values')
        if p < max(b, e) or row['peak_growth_bytes'] != p-b or row['end_growth_bytes'] != e-b:
            raise ValueError('Inconsistent memory measurements')
        if not row['gc_enabled']:
            raise ValueError('Garbage collection disabled')
        if row['evaluator'] == 'control':
            if row['evaluated'] or row['correct'] is not None or not row['control_input_preserved']:
                raise ValueError('Control performed evaluation')
        elif row['correct'] is not True or not row['evaluated']:
            raise ValueError('Incorrect evaluator output')
    for row in rows:
        if json.loads((directory / (row['evaluator']+'.json')).read_text()) != row:
            raise ValueError('Per-worker JSON does not match raw observations')
    saved = list(csv.DictReader((directory / 'raw_samples.csv').open()))
    if saved != [{key: '' if r.get(key) is None else str(r[key]) for key in FIELDS} for r in rows]:
        raise ValueError('CSV does not match JSON')
    for name, digest in meta['source_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Source differs from saved pilot: '+name)
    return dict(status='passed', observations=3, isolated_processes=3,
                correct_evaluators=2, units='bytes')


def collect(output):
    directory = output.resolve()
    if directory.parent != MEMORY_ROOT.resolve():
        raise ValueError('Output must be a fresh run directory directly under research_results/cek/memory')
    directory.mkdir(parents=True, exist_ok=False)
    meta = dict(schema_version=1, kind='pilot_only', units='bytes',
                created_at_utc=datetime.now(timezone.utc).isoformat(),
                source_commit=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                source_status=git('status', '--porcelain=v1', '--untracked-files=all'),
                source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES},
                command=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                observations='identity n=10; one fresh process each: current, cek, control',
                tracing='tracemalloc, one traceback frame, starts before construction',
                preparation='nameless builders; no remove_name conversion; no warmup/pre-evaluation',
                gc='automatic enabled; one gc.collect after input construction, before baseline',
                boundary='complete fully_eval(steps=10000) or CEK evaluate including initial_state and loop',
                retained='input, expected result, and evaluation result held through final read',
                control='same input and function-call boundary, returns input without evaluation',
                no_timing=True, no_rss=True, worker_timeout_seconds=60,
                limitations=['traced Python blocks, not total RSS or total allocated bytes',
                             'baseline includes prepared input; measurement bookkeeping adds small overhead',
                             'first evaluation, caches not prewarmed; single observation is not comparative evidence',
                             'source tree may be dirty; source hashes identify uncommitted harness'])
    write_json(directory / 'metadata.json', meta)
    rows = []
    for mode in MODES:
        row = run_worker(mode)
        # Preserve each completed worker, even if a subsequent observation fails.
        write_json(directory / (mode+'.json'), row)
        rows.append(row)
    write_json(directory / 'raw_samples.json', rows)
    with (directory / 'raw_samples.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in FIELDS} for row in rows)
    (directory / 'README.md').write_text('''# Traced-memory methodology pilot

Exactly one Identity n=10 observation per evaluator and a no-evaluation control.
All memory values are bytes. baseline is measured after preparation and GC;
peak is reset immediately before one call; ending is read with result alive.
Peak growth = peak - baseline; end growth = ending - baseline.
These describe traced live Python blocks, not RSS, cumulative allocations,
or a general evaluator ranking. The control is not subtracted automatically.
Source/command/environment and limitations are retained in metadata/raw JSON.
Run the coordinator with --verify-only --output this-directory to check saved data.
''')
    try:
        validation = verify(directory)
    except Exception as error:
        write_json(directory / 'validation.json', dict(status='failed', error=str(error)))
        raise
    write_json(directory / 'validation.json', validation)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--pilot', action='store_true', help='Only three Identity n=10 observations')
    mode.add_argument('--verify-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(args.output)))
    else:
        print(json.dumps(collect(args.output), indent=2))


if __name__ == '__main__':
    main()
