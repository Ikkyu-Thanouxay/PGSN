"""Pure-lambda recursion, without closure readback or evaluator extensions."""
import pytest

from pgsn import dsl
from pgsn.pgsn_term import Abs, App, Term, Variable
from cbv_cek import initial_state, step
from benchmark_recursion import countdown, check_current, check_cek
from metrics import measure_current, measure_cek


def bounded_cek(term, budget=10000):
    state = initial_state(term)
    for _ in range(budget):
        if state.halted:
            return state.control
        state = step(state)
    pytest.fail('CEK did not halt within the test budget')


def test_fix_forms_a_function_under_cbv():
    self, x = dsl.variable('self'), dsl.variable('x')
    maker = dsl.lambda_abs(self, dsl.lambda_abs(x, x))
    check_cek(bounded_cek(dsl.fix(maker)))
    # Contrast with old Y: CBV eagerly unfolds x x before it can enter maker.
    f = dsl.variable('f')
    old_y = dsl.lambda_abs(f, dsl.lambda_abs(x, f(x(x)))(dsl.lambda_abs(x, f(x(x)))))
    state = initial_state(old_y(maker))
    for _ in range(200):
        assert not state.halted
        state = step(state)


@pytest.mark.parametrize('size', [0, 1, 2, 5])
def test_recursive_countdown(size):
    term = countdown(size)
    pending = [term]
    while pending:
        node = pending.pop()
        assert not node.is_named
        assert type(node) in (Variable, Abs, App)
        if isinstance(node, Abs):
            pending.append(node.t)
        elif isinstance(node, App):
            pending.extend((node.t1, node.t2))
    check_current(term.fully_eval(steps=10000))
    check_cek(bounded_cek(term))
    result, current = measure_current(term)
    check_current(result)
    result, cek = measure_cek(term)
    check_cek(result)
    assert cek.builtin_applications == 0
    # Each successor adds one recursive traversal, not a constant shortcut.
    assert current.beta_reductions == 6 + 7 * size
    assert cek.closure_applications == cek.environment_extensions == 6 + 7 * size


def test_recursive_cek_has_no_production_fallback(monkeypatch):
    term = countdown(5)

    def forbidden(*args, **kwargs):
        raise AssertionError('Forbidden production evaluation operation')

    for name in ('fully_eval', 'eval', 'eval_or_none', 'shift', 'shift_or_none',
                 'subst', 'subst_or_none', 'remove_name'):
        monkeypatch.setattr(Term, name, forbidden)
    check_cek(bounded_cek(term))


def test_workload_uses_shared_dsl_fix(monkeypatch):
    def reached(maker):
        raise RuntimeError('shared fix reached')

    monkeypatch.setattr(dsl, 'fix', reached)
    with pytest.raises(RuntimeError, match='shared fix reached'):
        countdown(1)
