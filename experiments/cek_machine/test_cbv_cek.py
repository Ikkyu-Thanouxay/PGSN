"""Milestone 1 semantics and transition tests, importing the CEK directly."""
import pytest

from pgsn.dsl import (
    boolean, constant, div, integer, lambda_abs, minus, mod, plus, string,
    times, variable,
)
from pgsn.pgsn_term import Abs, App, Integer, Plus, Term, Variable
from cbv_cek import (
    AppArgument, AppFunction, Closure, Halt, PartialBuiltin, State,
    UnsupportedTermError, evaluate, initial_state, is_value, step,
)

x, y, f = variable('x'), variable('y'), variable('f')
identity = lambda_abs(x, x)


def test_explicit_transitions():
    state = initial_state(identity(integer(7)))
    term = state.control
    state = step(state)
    assert state.control is term.t1
    assert isinstance(state.continuation, AppFunction)
    assert state.continuation.argument is term.t2
    assert state.continuation.env == ()
    assert isinstance(state.continuation.continuation, Halt)
    state = step(state)
    closure = state.control
    assert isinstance(closure, Closure)
    state = step(state)
    assert state.control is term.t2
    assert isinstance(state.continuation, AppArgument)
    assert state.continuation.function is closure
    state = step(state)
    assert state.control is closure.body
    assert state.environment == (term.t2,)
    assert isinstance(state.continuation, Halt)
    assert not state.halted
    state = step(state)
    assert state.halted
    assert state.control == Integer.nameless(value=7)
    assert step(state) is state


@pytest.mark.parametrize('term, expected', [
    (identity(integer(5)), 5),
    (lambda_abs(x, integer(1))(integer(5)), 1),
    (lambda_abs(x, lambda_abs(y, x))(integer(5))(integer(10)), 5),
    (lambda_abs(f, f(integer(5)))(identity), 5),
    (identity(identity(integer(7))), 7),
    (lambda_abs(x, lambda_abs(x, x))(integer(5))(integer(10)), 10),
])
def test_lambda_comparisons(term, expected):
    assert evaluate(term) == term.fully_eval() == Integer.nameless(value=expected)


@pytest.mark.parametrize('term', [integer(7), string('hello'), boolean(True), constant('unit')])
def test_primitive_values(term):
    assert evaluate(term) == term.fully_eval()


@pytest.mark.parametrize('builtin, expected', [(plus, 10), (minus, 4), (times, 21), (div, 2), (mod, 1)])
def test_arithmetic(builtin, expected):
    term = builtin(integer(7), integer(3))
    assert evaluate(term) == term.fully_eval() == Integer.nameless(value=expected)


def test_builtin_passed_as_function():
    term = lambda_abs(f, f(integer(7), integer(3)))(plus)
    assert evaluate(term) == term.fully_eval() == Integer.nameless(value=10)


def test_partial_builtin():
    result = evaluate(plus(integer(7)))
    assert isinstance(result, PartialBuiltin)
    assert type(result.builtin) is Plus
    assert result.args == (Integer.nameless(value=7),)


def test_partial_stores_evaluated_expression():
    result = evaluate(plus(times(integer(2), integer(3))))
    assert isinstance(result, PartialBuiltin)
    assert result.args == (Integer.nameless(value=6),)
    assert all(is_value(arg) for arg in result.args)


def test_partial_applied_later():
    term = lambda_abs(f, f(integer(4)))(plus(times(integer(2), integer(3))))
    assert evaluate(term) == term.fully_eval() == Integer.nameless(value=10)


def test_unused_argument_is_strict():
    term = lambda_abs(x, integer(1))(div(integer(1), integer(0)))
    assert term.fully_eval() == Integer.nameless(value=1)
    with pytest.raises(ZeroDivisionError):
        evaluate(term)


def test_function_before_argument(monkeypatch):
    events = []
    original = Plus._apply_args

    def track(self, args):
        events.append(tuple(arg.value for arg in args))
        return original(self, args)

    monkeypatch.setattr(Plus, '_apply_args', track)
    term = lambda_abs(x, identity)(plus(integer(1), integer(2)))(plus(integer(3), integer(4)))
    assert evaluate(term).value == 7
    assert events == [(1, 2), (3, 4)]


def test_argument_environment_restored():
    term = lambda_abs(x, lambda_abs(y, lambda_abs(x, y))(integer(8))(x))(integer(3))
    assert evaluate(term) == term.fully_eval() == Integer.nameless(value=8)


def test_closure_captures_values():
    result = evaluate(lambda_abs(x, lambda_abs(y, x))(plus(integer(2), integer(3))))
    assert isinstance(result, Closure)
    assert result.env == (Integer.nameless(value=5),)


def test_no_fallback(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Forbidden production operation')

    for name in ('fully_eval', 'eval', 'eval_or_none', 'shift', 'shift_or_none', 'subst', 'subst_or_none'):
        monkeypatch.setattr(Term, name, forbidden)
    term = lambda_abs(x, plus(x, times(x, integer(2))))(div(integer(9), integer(3)))
    assert evaluate(term) == Integer.nameless(value=9)


@pytest.mark.parametrize('term, error', [
    (integer(1)(integer(2)), TypeError),
    (plus(string('bad'), integer(1)), TypeError),
    (plus(identity, integer(1)), TypeError),
    (variable('free'), LookupError),
])
def test_explicit_errors(term, error):
    with pytest.raises(error):
        evaluate(term)


def test_unsupported_term():
    # Reject an unselected scalar builtin; no later-milestone support needed.
    from pgsn.pgsn_term import Equal
    with pytest.raises(UnsupportedTermError, match='Equal'):
        evaluate(Equal.named())


def test_deep_nameless_evaluation_uses_machine_stack():
    # Bypass the recursive entry-boundary name conversion deliberately.
    ident = Abs.nameless(v=None, t=Variable.nameless(num=0))
    term = Integer.nameless(value=7)
    for _ in range(2000):
        term = App.term(ident, term)
    assert evaluate(term) == Integer.nameless(value=7)
