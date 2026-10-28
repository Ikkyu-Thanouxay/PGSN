"""Small correctness and data-safety checks, not performance benchmarks."""
import json
from pathlib import Path
import subprocess
import sys
import tracemalloc

import pytest

import benchmark_memory as harness
import memory_worker as worker


@pytest.mark.parametrize('family', ['identity', 'captured'])
@pytest.mark.parametrize('mode', ['current', 'cek'])
def test_tiny_successful_inputs(family, mode):
    row = worker.observe(family, 1, mode)
    assert row['status'] == 'ok' and row['correct'] is True
    assert row['peak_bytes'] >= max(row['baseline_bytes'], row['ending_bytes'])
    assert row['peak_growth_bytes'] == row['peak_bytes']-row['baseline_bytes']
    assert row['end_growth_bytes'] == row['ending_bytes']-row['baseline_bytes']
    assert not tracemalloc.is_tracing()
    assert not any('seconds' in key or 'duration' in key for key in row)


def test_control_does_not_evaluate(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail('Control must not call an evaluator')
    monkeypatch.setitem(worker.EVALUATORS, 'current', fail)
    monkeypatch.setitem(worker.EVALUATORS, 'cek', fail)
    row = worker.observe('identity', 1, 'control')
    assert row['status'] == 'ok' and not row['evaluated']
    assert row['correct'] is None and row['control_input_preserved']


def test_boundary_and_correctness_after_measurement(monkeypatch):
    events = []
    class Term:
        is_named = False
        def __eq__(self, other):
            assert not tracemalloc.is_tracing()
            events.append('correctness')
            return True
    term = Term()
    def build(size):
        assert tracemalloc.is_tracing()
        events.append('build')
        return term, term
    def run(value):
        assert tracemalloc.is_tracing() and value is term
        events.append('evaluate')
        return value
    monkeypatch.setitem(worker.BUILDERS, 'identity', build)
    monkeypatch.setitem(worker.EVALUATORS, 'cek', run)
    row = worker.observe('identity', 1, 'cek')
    assert row['status'] == 'ok'
    assert events == ['build', 'evaluate', 'correctness']


def test_error_is_retained_and_tracing_stops(monkeypatch):
    def fail(term):
        raise RuntimeError('deliberate fixture error')
    monkeypatch.setitem(worker.EVALUATORS, 'cek', fail)
    row = worker.observe('identity', 1, 'cek')
    assert row['status'] == 'error' and row['error_type'] == 'RuntimeError'
    assert row['peak_bytes'] is None and not tracemalloc.is_tracing()


def test_worker_cli_isolated():
    command = [sys.executable, '-B', str(Path(worker.__file__)),
               '--family', 'captured', '--size', '1', '--evaluator', 'cek']
    process = subprocess.run(command, capture_output=True, text=True, check=True)
    row = json.loads(process.stdout)
    assert row['correct'] is True and not process.stderr


def fake_row(mode):
    return dict(family='identity', size=10, evaluator=mode,
                pid=100+harness.MODES.index(mode), status='ok',
                correct=None if mode=='control' else True, evaluated=mode!='control',
                baseline_bytes=100, peak_bytes=150, ending_bytes=110,
                peak_growth_bytes=50, end_growth_bytes=10, gc_enabled=True,
                control_input_preserved=mode=='control')


def test_output_and_refusal_and_saved_verification(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, 'MEMORY_ROOT', tmp_path)
    monkeypatch.setattr(harness, 'run_worker', fake_row)
    output = tmp_path / 'new-run'
    harness.collect(output)
    assert {p.name for p in output.iterdir()} == {
        'metadata.json', 'raw_samples.json', 'raw_samples.csv', 'validation.json',
        'current.json', 'cek.json', 'control.json', 'README.md'}
    assert harness.verify(output)['status'] == 'passed'
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        harness.collect(output)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(ValueError, match='fresh run directory'):
        harness.collect(tmp_path / 'outside' / 'run')
    rows = json.loads((output/'raw_samples.json').read_text())
    rows[0]['peak_growth_bytes'] = 999
    (output/'raw_samples.json').write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='Inconsistent'):
        harness.verify(output)


def test_failed_observation_retained(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, 'MEMORY_ROOT', tmp_path)
    def wrong(mode):
        row = fake_row(mode)
        if mode == 'cek':
            row.update(status='incorrect_result', correct=False)
        return row
    monkeypatch.setattr(harness, 'run_worker', wrong)
    output = tmp_path/'failed-run'
    with pytest.raises(ValueError):
        harness.collect(output)
    assert json.loads((output/'validation.json').read_text())['status']=='failed'
    assert json.loads((output/'raw_samples.json').read_text())[1]['correct'] is False
