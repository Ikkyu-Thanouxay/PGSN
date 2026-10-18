"""Fast fixtures only: no real slow programs."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import current_pgsn_benchmark as benchmark
import current_pgsn_worker as worker


@pytest.mark.parametrize('duration,expected', [(0.099, (5, 50)), (0.1, (3, 20)),
    (1, (2, 10)), (10, (1, 5)), (60, (0, 3))])
def test_policy_boundaries(duration, expected):
    assert benchmark.policy(duration) == expected


def test_statistics():
    result = benchmark.statistics_for([1, 2, 3, 4])
    assert result['median'] == 2.5
    assert result['q1'] == 1.75
    assert result['q3'] == 3.25
    assert result['iqr'] == 1.5
    assert result['stdev'] == pytest.approx(1.2909944487358056)


def test_dependencies_include_transitive_bytes_and_hashes(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'ROOT', tmp_path)
    (tmp_path / 'main.xml').write_text('<PGSN><from file="a.xml"/></PGSN>')
    (tmp_path / 'a.xml').write_text('<PGSNModule><from file="b.xml"/></PGSNModule>')
    (tmp_path / 'b.xml').write_text('<PGSNModule><from file="a.xml"/></PGSNModule>')
    deps, unresolved = benchmark.dependencies(tmp_path / 'main.xml')
    assert not unresolved
    assert [r['path'] for r in deps] == ['a.xml', 'b.xml']
    assert deps[1]['sha256'] == hashlib.sha256((tmp_path / 'b.xml').read_bytes()).hexdigest()


def test_counter_restores_methods_on_exception():
    from pgsn.pgsn_term import Term, Context
    originals = Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none
    with pytest.raises(RuntimeError), worker.counters():
        raise RuntimeError('fixture')
    assert (Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none) == originals


def test_small_pipeline_does_not_reevaluate_during_conversion(monkeypatch):
    from pgsn.dsl import lambda_abs, variable
    from pgsn.pgsn_term import Term
    term = lambda_abs(variable('x'), variable('x'))(7)
    original = Term.fully_eval
    calls = []

    def evaluate(self, steps):
        calls.append(self)
        return original(self, steps)
    monkeypatch.setattr(worker, 'load_term', lambda path: term)
    monkeypatch.setattr(Term, 'fully_eval', evaluate)
    one = worker.run('fixture')
    assert one['status'] == 'ok', one
    assert len(calls) == 1
    two = worker.run('fixture')
    assert two['output_sha256'] == one['output_sha256']


def test_counter_counts_small_beta(monkeypatch):
    from pgsn.dsl import lambda_abs, variable
    term = lambda_abs(variable('x'), variable('x'))(7)
    monkeypatch.setattr(worker, 'load_term', lambda path: term)
    result = worker.run('fixture', 'counters')
    assert result['status'] == 'ok'
    assert result['counts']['root_reductions'] == 1
    assert result['counts']['beta_reductions'] == 1
    assert not any(key in result for key in worker.TIMINGS)


def test_unregistered_python_rejected_before_import():
    with pytest.raises(ValueError, match='not explicitly registered'):
        worker.load_term('examples/robot.py')


def test_timeout_preserved(monkeypatch):
    import subprocess
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('fixture', 1)
    monkeypatch.setattr(benchmark.subprocess, 'run', timeout)
    result = benchmark.worker('fixture', 'clean', 10, 1)
    assert result['status'] == 'timeout'
    assert result['process_wall_seconds'] >= 0


def test_registry_and_wrapper_dependencies():
    rows = benchmark.sources()
    assert len(rows) == 53
    assert sum(r['root_type'] == 'PGSN' for r in rows) == 24
    assert sum(r['root_type'] == 'PGSNModule' for r in rows) == 17
    assert sum(r['language'] == 'python' for r in rows) == 12
    module = next(r for r in rows if r['path'].endswith('/eu_ai_act_full.xml'))
    assert module['status'] == 'module_not_standalone'
    for path in benchmark.PROFILES[1:]:
        row = next(r for r in rows if r['path'] == path)
        assert 'examples/EU_AI_ACT/eu_ai_act_full.xml' in [d['path'] for d in row['dependencies']]


def test_hash_instability_rejected():
    src = [dict(path='fixture', status='eligible', reason='')]
    pilot = dict(path='fixture', status='ok', output_sha256='one')
    sample = dict(path='fixture', phase='measured', status='ok', output_sha256='two')
    with pytest.raises(ValueError, match='instability'):
        benchmark.aggregate(src, [sample], [pilot])
