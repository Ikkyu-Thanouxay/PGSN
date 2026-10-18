"""Sequential fresh-process real-example research benchmark and saved-data verifier."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from current_pgsn_worker import ROOT, PYTHON_ENTRIES, TIMINGS, environment

PROFILES = ['examples/SolarWinds.xml'] + [
    'examples/EU_AI_ACT/case_' + name + '.xml'
    for name in ['proctoring', 'medical_ai', 'gpai_system', 'recruitment_ai']]


def now():
    return datetime.now(timezone.utc).isoformat()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def policy(seconds):
    for boundary, warmups, runs in [(0.1, 5, 50), (1, 3, 20), (10, 2, 10), (60, 1, 5)]:
        if seconds < boundary:
            return warmups, runs
    return 0, 3


def statistics_for(values):
    q1, _, q3 = statistics.quantiles(values, n=4, method='inclusive') if len(values) > 1 else [values[0]] * 3
    return dict(n=len(values), median=statistics.median(values), mean=statistics.mean(values),
                stdev=statistics.stdev(values) if len(values) > 1 else None,
                q1=q1, q3=q3, iqr=q3-q1, min=min(values), max=max(values))


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def csv_write(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                             for k, v in row.items()})


def dependencies(path):
    seen = set()
    unresolved = []

    def visit(current):
        for node in ET.parse(current).getroot().iter('from'):
            spec = node.get('file')
            if not spec:
                continue
            dependency = (current.parent / spec).resolve()
            if spec.startswith('/') or not dependency.is_relative_to(ROOT) or not dependency.is_file():
                unresolved.append(dict(source=str(current.relative_to(ROOT)), spec=spec))
                continue
            if dependency == path.resolve() or dependency in seen:
                continue
            seen.add(dependency)
            visit(dependency)
    visit(path.resolve())
    return [dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size,
                 sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(seen)], unresolved


def sources():
    registry = list(csv.DictReader((ROOT / 'research_results/examples.csv').open()))
    rows = []
    for entry in registry:
        path = ROOT / entry['path']
        deps, unresolved = dependencies(path) if entry['language'] == 'xml' else ([], [])
        status = ('module_not_standalone' if entry['root_type'] == 'PGSNModule' else
                  'eligible' if entry['language'] == 'xml' or entry['path'] in PYTHON_ENTRIES else
                  'not_safely_benchmarkable')
        rows.append(dict(path=entry['path'], language=entry['language'], root_type=entry['root_type'],
                         standalone_evaluation=entry['standalone_evaluation'], status=status,
                         reason=entry['reason_if_not_automatic'] if status == 'not_safely_benchmarkable' else '',
                         role=entry['notes_role'], bytes=path.stat().st_size,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         git_blob=git('hash-object', str(path)), dependencies=deps,
                         unresolved_dependencies=unresolved,
                         aggregate_dependency_bytes=sum(d['bytes'] for d in deps),
                         source_plus_dependency_bytes=path.stat().st_size + sum(d['bytes'] for d in deps),
                         python_entry=PYTHON_ENTRIES.get(entry['path'], ''),
                         python_dependency_scope='PGSN library at source commit; standard/package imports; no local XML' if entry['language'] == 'python' else 'not-applicable'))
    return rows


def worker(path, mode, steps, timeout):
    command = [sys.executable, str(Path(__file__).with_name('current_pgsn_worker.py')),
               '--path', path, '--mode', mode, '--steps', str(steps)]
    started = now()
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        elapsed = time.perf_counter() - t0
        if proc.returncode or proc.stderr:
            result = dict(path=path, mode=mode, status='error', error=proc.stderr, stdout=proc.stdout)
        else:
            result = json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - t0
        result = dict(path=path, mode=mode, status='timeout', error=f'Worker exceeded {timeout} seconds')
    result.update(started_at=started, completed_at=now(), timeout_seconds=timeout)
    result['process_wall_seconds' if mode == 'clean' else 'diagnostic_process_wall_seconds'] = elapsed
    return result


def compact(result):
    return {k: v for k, v in result.items() if k not in ('profile', 'environment')}


def aggregate(source_rows, samples, pilots):
    summaries = []
    for source in source_rows:
        path = source['path']
        selected = [r for r in samples if r['path'] == path]
        measured = [r for r in selected if r['phase'] == 'measured']
        pilot = next((r for r in pilots if r['path'] == path), None)
        status = source['status']
        if pilot:
            status = pilot['status']
        if selected:
            failures = [r for r in selected if r['status'] != 'ok']
            status = failures[0]['status'] if failures else 'ok'
        hashes = {r['output_sha256'] for r in ([pilot] if pilot else []) + selected if r['status'] == 'ok'}
        if len(hashes) > 1:
            raise ValueError('Output hash instability: ' + path)
        row = dict(path=path, status=status, reason=source['reason'], measured_samples=len(measured),
                   output_sha256=next(iter(hashes), ''), output_bytes=pilot.get('output_bytes', '') if pilot else '')
        if status == 'ok':
            if len(measured) != pilot['selected_runs']:
                raise ValueError('Incomplete measured runs: ' + path)
            for field in TIMINGS:
                for key, value in statistics_for([r[field] for r in measured]).items():
                    row[field + '_' + key] = value
        summaries.append(row)
    return summaries


def verify(directory):
    meta = json.loads((directory / 'metadata.json').read_text())
    src = list(csv.DictReader((directory / 'sources.csv').open()))
    assert len(src) == 53
    assert sum(r['root_type'] == 'PGSN' for r in src) == 24
    assert sum(r['root_type'] == 'PGSNModule' for r in src) == 17
    assert sum(r['language'] == 'python' for r in src) == 12
    pilots = json.loads((directory / 'pilot.json').read_text())
    samples = json.loads((directory / 'raw_samples.json').read_text())
    for source in src:
        p = ROOT / source['path']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == source['sha256']
        for dep in json.loads(source['dependencies']):
            assert hashlib.sha256((ROOT / dep['path']).read_bytes()).hexdigest() == dep['sha256']
        if source['status'] != 'eligible':
            assert not any(r['path'] == source['path'] for r in pilots + samples)
    eligible = {r['path'] for r in src if r['status'] == 'eligible'}
    assert {r['path'] for r in pilots} == eligible
    for pilot in pilots:
        assert pilot['mode'] == 'clean'
        if pilot['status'] == 'ok':
            assert (pilot['selected_warmups'], pilot['selected_runs']) == policy(pilot['worker_total_seconds'])
            chosen = [r for r in samples if r['path'] == pilot['path']]
            if all(r['status'] == 'ok' for r in chosen):
                assert sum(r['phase'] == 'warmup' for r in chosen) == pilot['selected_warmups']
                assert sum(r['phase'] == 'measured' for r in chosen) == pilot['selected_runs']
    for row in pilots + samples:
        assert row['mode'] == 'clean' and 'counts' not in row and 'profile' not in row
    # Recompute every summary field from persisted raw values.
    expected = aggregate(src, samples, pilots)
    actual = list(csv.DictReader((directory / 'summary.csv').open()))
    assert len(actual) == len(expected)
    for a, b in zip(actual, expected):
        for key, value in b.items():
            assert a[key] == ('' if value is None else str(value)), (key, a[key], value)
    for name, rows in [('pilot', pilots), ('raw_samples', samples)]:
        saved = list(csv.DictReader((directory / (name + '.csv')).open()))
        assert len(saved) == len(rows)
        for a, b in zip(saved, rows):
            for key, value in compact(b).items():
                text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                assert a[key] == text
    counter_rows = json.loads((directory / 'counters.json').read_text())
    successful = {r['path'] for r in expected if r['status'] == 'ok'}
    assert {r['path'] for r in counter_rows} == successful
    profile_files = list((directory / 'profiles').glob('*.json'))
    assert {json.loads(p.read_text())['path'] for p in profile_files} == set(PROFILES)
    for diagnostic in counter_rows:
        assert diagnostic['mode'] == 'counters' and not any(k in diagnostic for k in TIMINGS)
        if diagnostic['status'] == 'ok':
            assert diagnostic['output_sha256'] == next(r['output_sha256'] for r in expected if r['path'] == diagnostic['path'])
    for p in profile_files:
        diagnostic = json.loads(p.read_text())
        assert diagnostic['mode'] == 'profile' and not any(k in diagnostic for k in TIMINGS)
        if diagnostic['status'] == 'ok':
            assert diagnostic['output_sha256'] == next(r['output_sha256'] for r in expected if r['path'] == diagnostic['path'])
    assert meta['source_dirty'] is False
    return dict(status='passed', sources=len(src), pilots=len(pilots), raw_rows=len(samples),
                successfully_measured=sum(r['status'] == 'ok' for r in expected))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--diagnostic-timeout', type=int, default=3600)
    parser.add_argument('--steps', type=int, default=1_000_000)
    args = parser.parse_args()
    directory = args.output.resolve()
    if args.verify_only:
        print(json.dumps(verify(directory)))
        return
    if git('status', '--porcelain'):
        raise RuntimeError('Measurements require a clean source/harness commit')
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'profiles').mkdir()
    meta = dict(branch=git('branch', '--show-current'), source_commit=git('rev-parse', 'HEAD'),
                source_dirty=False, source_status=git('status', '--porcelain'),
                environment=environment(), command=sys.argv, started_at=now(),
                step_budget=args.steps, timeout_seconds=args.timeout,
                diagnostic_timeout_seconds=args.diagnostic_timeout,
                run_order='all pilots; per-input warmups then measured; counters; profiles; sequential fresh workers',
                policy_basis='pilot worker_total_seconds; process startup excluded',
                policy=[dict(less_than_s=b, warmups=w, runs=n) for b, w, n in
                        [(0.1, 5, 50), (1, 3, 20), (10, 2, 10), (60, 1, 5), ('infinity', 0, 3)]],
                gc_policy='default enabled, no explicit collection or threshold changes',
                timing_units='seconds', output_policy='Tree.show UTF-8; sorting=False; idhidden=True; ascii-ex',
                counter_scope='initial name removal excluded; same CEK research visit definitions',
                profiler_scope='fully_eval only, including name removal; no counters', status='running')
    dump(directory / 'metadata.json', meta)
    source_rows = sources()
    csv_write(directory / 'sources.csv', source_rows)
    pilots, samples, diagnostics = [], [], []
    for source in source_rows:
        if source['status'] != 'eligible':
            continue
        print('pilot ' + source['path'], flush=True)
        result = worker(source['path'], 'clean', args.steps, args.timeout)
        if result['status'] == 'ok':
            result['selected_warmups'], result['selected_runs'] = policy(result['worker_total_seconds'])
        pilots.append(result)
        dump(directory / 'pilot.json', pilots)
        csv_write(directory / 'pilot.csv', [compact(r) for r in pilots])
    # Pilot selections are persisted before any main measurement.
    for pilot in pilots:
        if pilot['status'] != 'ok':
            continue
        print(f"main {pilot['path']} warmups={pilot['selected_warmups']} runs={pilot['selected_runs']}", flush=True)
        for phase, count in [('warmup', pilot['selected_warmups']), ('measured', pilot['selected_runs'])]:
            if not count:
                continue
            for index in range(count):
                result = worker(pilot['path'], 'clean', args.steps, args.timeout)
                result.update(phase=phase, iteration=index + 1)
                if result['status'] == 'ok' and result['output_sha256'] != pilot['output_sha256']:
                    dump(directory / 'hash_failure.json', result)
                    raise RuntimeError('Unstable output; stop before committing data')
                samples.append(result)
                dump(directory / 'raw_samples.json', samples)
                csv_write(directory / 'raw_samples.csv', [compact(r) for r in samples])
                if result['status'] != 'ok':
                    break
            if samples[-1]['status'] != 'ok':
                break
    summary = aggregate(source_rows, samples, pilots)
    csv_write(directory / 'summary.csv', summary)
    successful = {r['path'] for r in summary if r['status'] == 'ok'}
    for path in [r['path'] for r in source_rows if r['path'] in successful]:
        print('counters ' + path, flush=True)
        diagnostics.append(worker(path, 'counters', args.steps, args.diagnostic_timeout))
        dump(directory / 'counters.json', diagnostics)
        csv_write(directory / 'counters.csv', [compact(r) for r in diagnostics])
    for path in PROFILES:
        print('profile ' + path, flush=True)
        result = worker(path, 'profile', args.steps, args.diagnostic_timeout)
        result.update(source_commit=meta['source_commit'], profiler_scope=meta['profiler_scope'])
        stem = path.removeprefix('examples/').replace('/', '__').removesuffix('.xml')
        dump(directory / 'profiles' / (stem + '.json'), result)
        report = result.get('profile', {}).get('readable_report', result.get('error', 'No report'))
        (directory / 'profiles' / (stem + '.txt')).write_text(
            f"Input: {path}\nSource/harness: {meta['source_commit']}\nStatus: {result['status']}\nScope: {meta['profiler_scope']}\n\n" + report)
    meta.update(status='complete', completed_at=now())
    dump(directory / 'metadata.json', meta)
    validation = verify(directory)
    dump(directory / 'validation.json', validation)
    print(json.dumps(validation), flush=True)


if __name__ == '__main__':
    main()
