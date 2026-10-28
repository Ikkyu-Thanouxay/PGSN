"""Fixed cold-memory experiment: 120 evaluator observations and 60 controls."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import distributions
import os
import json
from pathlib import Path
import subprocess
import sys

from benchmark_memory import ROOT, MEMORY_ROOT, FIELDS, git, write_json

FAMILIES = ('identity', 'captured')
SIZES = (10, 100, 200)
RUNS = 10
MEMORY_FIELDS = ('baseline_bytes', 'peak_bytes', 'ending_bytes',
                 'peak_growth_bytes', 'end_growth_bytes')
CSV_FIELDS = ('observation', 'repetition', *FIELDS)


def schedule():
    """Alternate evaluator order; ten separate controls for each configuration."""
    for family in FAMILIES:
        for size in SIZES:
            for repetition in range(1, RUNS+1):
                modes = ('current', 'cek', 'control') if repetition % 2 else ('cek', 'current', 'control')
                for mode in modes:
                    yield family, size, repetition, mode


def run_worker(family, size, mode):
    command = [sys.executable, '-B', str(Path(__file__).with_name('memory_worker.py')),
               '--family', family, '--size', str(size), '--evaluator', mode]
    row = dict(family=family, size=size, evaluator=mode, status='worker_error', command=command)
    try:
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        row.update(returncode=process.returncode, stderr=process.stderr)
        try:
            worker = json.loads(process.stdout)
            if not isinstance(worker, dict):
                raise ValueError('Worker JSON is not an object')
            if (worker.get('family'), worker.get('size'), worker.get('evaluator')) != (family, size, mode):
                raise ValueError('Worker returned the wrong condition')
            row.update(worker)
            if process.returncode or process.stderr:
                row['status'] = 'worker_error'
        except (ValueError, TypeError) as error:
            row.update(error_type=type(error).__name__, error=str(error), stdout=process.stdout)
    except subprocess.TimeoutExpired as error:
        row.update(error_type=type(error).__name__, error=str(error),
                   stdout=str(error.stdout), stderr=str(error.stderr))
    except OSError as error:
        row.update(error_type=type(error).__name__, error=str(error))
    return row


def csv_projection(rows):
    return [{key: '' if r.get(key) is None else str(r[key]) for key in CSV_FIELDS} for r in rows]


def verify(directory):
    """Recheck observations and source provenance without evaluating any terms."""
    rows = json.loads((directory/'raw_samples.json').read_text())
    meta = json.loads((directory/'metadata.json').read_text())
    expected = list(schedule())
    if len(rows) != len(expected) or meta['expected_observations'] != len(expected):
        raise ValueError('Missing or extra observations')
    errors, pids = [], []
    environments = set()
    for index, (row, condition) in enumerate(zip(rows, expected), 1):
        family, size, repetition, mode = condition
        if (row.get('family'), row.get('size'), row.get('repetition'), row.get('evaluator')) != condition:
            raise ValueError('Unexpected condition/order')
        if row.get('observation') != index:
            raise ValueError('Invalid observation identifier')
        if json.loads((directory/'observations'/f'{index:03}.json').read_text()) != row:
            raise ValueError('Individual observation differs from combined raw JSON')
        if row['status'] != 'ok':
            errors.append(row)
            continue
        pids.append(row['pid'])
        if not row['gc_enabled'] or row['recursion_limit'] != meta['recursion_limit']:
            raise ValueError('GC or recursion policy differs')
        environments.add((row['python'], row['executable'], row['platform'], tuple(row['gc_thresholds'])))
        b, p, e = (row[k] for k in MEMORY_FIELDS[:3])
        if not all(type(v) is int and v >= 0 for v in (b, p, e)):
            raise ValueError('Invalid bytes')
        if p < max(b, e) or row['peak_growth_bytes'] != p-b or row['end_growth_bytes'] != e-b:
            raise ValueError('Memory arithmetic mismatch')
        if mode == 'control':
            if row['evaluated'] or row['correct'] is not None or not row['control_input_preserved']:
                raise ValueError('Invalid no-evaluation control')
        elif row['correct'] is not True or not row['evaluated'] or row['result'] != row['expected']:
            raise ValueError('Incorrect evaluator result')
    # Each observation is a separate subprocess.run exec invocation. Also audit PIDs.
    if len(set(pids)) != len(pids):
        raise ValueError('Repeated worker PID; inspect process isolation')
    if len(environments) != 1:
        raise ValueError('Inconsistent worker environments')
    saved = list(csv.DictReader((directory/'raw_samples.csv').open()))
    if saved != csv_projection(rows):
        raise ValueError('CSV differs from raw JSON')
    if json.loads((directory/'errors.json').read_text()) != errors:
        raise ValueError('Error inventory differs from raw observations')
    for name, digest in meta['source_sha256'].items():
        content = subprocess.check_output(['git', 'show', meta['source_commit']+':'+name], cwd=ROOT)
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError('Committed source hash mismatch: '+name)
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Working source changed since run: '+name)
    for name, digest in meta['earlier_evidence_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Earlier evidence changed: '+name)
    return dict(status='passed' if not errors else 'passed_with_errors',
                observations=len(rows), evaluator_observations=sum(r['evaluator']!='control' for r in rows),
                controls=sum(r['evaluator']=='control' for r in rows),
                correct_evaluations=sum(r.get('correct') is True for r in rows),
                errors=len(errors), unique_successful_worker_pids=len(set(pids)), units='bytes')


def collect(output):
    directory = output.resolve()
    if directory.parent != MEMORY_ROOT.resolve():
        raise ValueError('Output must be directly under research_results/cek/memory')
    # Output is created only after confirming the implementation is committed.
    if git('status', '--porcelain=v1', '--untracked-files=all'):
        raise RuntimeError('Start from a clean committed implementation')
    sources = git('ls-files', 'src/pgsn', 'experiments/cek_machine', 'requirements.txt', 'pyproject.toml').splitlines()
    sources = [name for name in sources if name.endswith(('.py', '.txt', '.toml', '.md'))]
    earlier = git('ls-files', 'research_results').splitlines()
    meta = dict(schema_version=1, kind='full_cold_memory', units='bytes',
                created_at_utc=datetime.now(timezone.utc).isoformat(),
                source_commit=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                source_dirty=False, command=[sys.executable, '-B', *sys.argv], cwd=str(Path.cwd()),
                python=sys.version, executable=sys.executable, recursion_limit=sys.getrecursionlimit(),
                installed_distributions=sorted([(d.metadata['Name'],d.version) for d in distributions()]),
                python_flags=repr(sys.flags),
                python_environment={k:os.environ.get(k) for k in ('PYTHONHASHSEED','PYTHONMALLOC','PYTHONOPTIMIZE','PYTHONTRACEMALLOC')},
                source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
                earlier_evidence_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in earlier},
                families=list(FAMILIES), sizes=list(SIZES), runs_per_condition=RUNS,
                expected_observations=180, expected_evaluator_observations=120, expected_controls=60,
                order='family then size ascending; repetitions 1-10; alternate Current/CEK order; control last',
                isolation='one fresh subprocess interpreter and freshly built input per observation',
                tracing='tracemalloc.start(1) before construction; reset_peak immediately before one evaluation',
                gc='automatic enabled; one explicit gc.collect after construction, before baseline',
                cache_policy='first evaluation; no evaluator warmup, correctness pre-evaluation, or counter passes',
                preparation='existing nameless Identity/Captured builders; no actual remove_name conversion',
                boundary='complete fully_eval(steps=10000) or complete CEK evaluate including initial_state and loop',
                retained='input, expected result and result retained through final read; correctness checked afterward',
                no_timing=True, no_rss=True, worker_timeout_seconds=60,
                statistics='median; inclusive quartiles q1/q3; IQR=q3-q1; min/max; all raw observations retained',
                limitations=['traced live Python blocks, not total process memory or cumulative allocations',
                             'bookkeeping overhead present; controls retained, not automatically subtracted',
                             'one platform/session; two shared workloads and three sizes; no general ranking or asymptotic claim',
                             'cold means first evaluator call, not cold interpreter/OS caches'])
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'observations').mkdir()
    write_json(directory/'metadata.json', meta)
    rows = []
    for index, (family, size, repetition, mode) in enumerate(schedule(), 1):
        row = run_worker(family, size, mode)
        row.update(observation=index, repetition=repetition)
        write_json(directory/'observations'/f'{index:03}.json', row)
        rows.append(row)
        if index % 30 == 0:
            print(f'Retained {index}/180 observations', flush=True)
    write_json(directory/'raw_samples.json', rows)
    with (directory/'raw_samples.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(csv_projection(rows))
    write_json(directory/'errors.json', [r for r in rows if r['status']!='ok'])
    try:
        validation = verify(directory)
    except Exception as error:
        write_json(directory/'validation.json', dict(status='failed', error=str(error)))
        raise
    write_json(directory/'validation.json', validation)
    return validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--full', action='store_true')
    mode.add_argument('--verify-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.output) if args.verify_only else collect(args.output)
    print(json.dumps(result))
    return 0 if result['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
