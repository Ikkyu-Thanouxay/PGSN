"""Milestone 1 semantics and transition tests, importing the CEK directly."""
import pytest

from pgsn.dsl import (
    boolean, constant, div, integer, lambda_abs, minus, mod, plus, string,
    times, variable, record, list_term, overwrite_record,
)
from pgsn.pgsn_term import Abs, App, Integer, Plus, Term, Variable
from cbv_cek import (
    AppArgument, AppFunction, Closure, Halt, PartialBuiltin, State,
    ExperimentalStuckError, UnsupportedTermError, evaluate, initial_state,
    is_value, step, RecordField, RecordValue,
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
    with pytest.raises(ExperimentalStuckError):
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


# Basic records: strict insertion-order field evaluation, primitive fields only.
# Production tests/test_record.py provides the shared field-lookup examples.
@pytest.mark.parametrize('fields,key', [
    ({'count': integer(7)}, 'count'),
    ({'description': string('assessment'), 'applies': boolean(True)}, 'description'),
    ({'description': string('assessment'), 'applies': boolean(True)}, 'applies'),
    ({'count': plus(integer(2), integer(3))}, 'count'),
    ({'status': constant('unknown')}, 'status'),
])
def test_record_lookup_shared_cases(fields, key):
    term = record(fields)(string(key))
    assert evaluate(term) == term.fully_eval()


def test_record_value_and_empty_record():
    term = record({'count': plus(integer(2), integer(3)), 'ok': boolean(True)})
    result = evaluate(term)
    assert isinstance(result, RecordValue) and is_value(result)
    assert result.fields == tuple(term.fully_eval().attributes().items())
    assert not isinstance(result, Term)  # No implicit runtime-to-Term readback.
    assert evaluate(record({})) == RecordValue(())


def test_record_passed_through_lambda_and_captured_by_closure():
    r = variable('r')
    lookup = lambda_abs(r, lambda_abs(x, r(string('count'))))
    argument = record({'count': integer(7)})
    closure = evaluate(lookup(argument))
    assert isinstance(closure, Closure)
    assert isinstance(closure.env[0], RecordValue)
    term = lookup(argument)(integer(0))
    assert evaluate(term) == term.fully_eval() == Integer.nameless(value=7)


def test_record_fields_restore_lexical_environment():
    # Evaluating first leaves a different environment; second must still see x.
    term = lambda_abs(x, record({
        'first': lambda_abs(y, y)(integer(9)), 'second': x,
    }))(integer(5))(string('second'))
    assert evaluate(term) == term.fully_eval() == Integer.nameless(value=5)


def test_record_continuation_transitions():
    state = initial_state(record({'a': integer(1), 'b': integer(2)}))
    assert not is_value(state.control)
    state = step(state)
    assert isinstance(state.continuation, RecordField)
    assert state.continuation.label == 'a'
    assert state.continuation.completed == ()
    state = step(state)
    assert state.control == Integer.nameless(value=2)
    assert isinstance(state.continuation, RecordField)
    assert state.continuation.label == 'b'
    assert state.continuation.completed == (('a', Integer.nameless(value=1)),)
    state = step(state)
    assert state.halted
    assert state.control == RecordValue((('a', Integer.nameless(value=1)),
                                         ('b', Integer.nameless(value=2))))


def test_record_fields_evaluated_once_in_insertion_order(monkeypatch):
    events = []
    original = Plus._apply_args
    def track(self, args):
        events.append(tuple(arg.value for arg in args))
        return original(self, args)
    monkeypatch.setattr(Plus, '_apply_args', track)
    # Labels deliberately oppose alphabetical order. Even unselected a runs.
    term = record({'z': plus(integer(1), integer(2)),
                   'a': plus(integer(3), integer(4))})(string('z'))
    assert evaluate(term) == Integer.nameless(value=3)
    assert events == [(1, 2), (3, 4)]


def test_record_missing_field_and_wrong_key_are_explicit_errors():
    missing = record({'count': integer(7)})(string('missing'))
    # Production retains an unresolved application; CEK raises explicitly.
    assert missing.fully_eval() == missing.remove_name()
    with pytest.raises(KeyError, match='Unknown record field.*missing'):
        evaluate(missing)
    with pytest.raises(TypeError, match='String key'):
        evaluate(record({'count': integer(7)})(integer(0)))


def test_record_unselected_invalid_field_is_still_strict():
    term = record({'good': integer(7), 'bad': div(integer(1), integer(0))})(string('good'))
    assert term.fully_eval() == Integer.nameless(value=7)
    with pytest.raises(ExperimentalStuckError):
        evaluate(term)


@pytest.mark.parametrize('value,description', [
    (identity, 'Closure'),
    (plus(integer(1)), 'PartialBuiltin'),
    (record({'nested': integer(1)}), 'RecordValue'),
    (list_term((integer(1),)), 'List'),
])
def test_record_unsupported_field_values(value, description):
    with pytest.raises(UnsupportedTermError, match=description):
        evaluate(record({'unsupported': value}))


def test_record_merging_remains_unsupported():
    with pytest.raises(UnsupportedTermError, match='OverwriteRecord'):
        evaluate(overwrite_record(record({}))(record({})))


def test_record_evaluation_has_no_production_fallback(monkeypatch):
    term = lambda_abs(x, record({'count': plus(x, integer(2))}))(integer(3))(string('count'))
    expected = term.fully_eval()
    def forbidden(*args, **kwargs):
        raise AssertionError('Forbidden production evaluation operation')
    for name in ('fully_eval', 'eval', 'eval_or_none', 'shift', 'shift_or_none', 'subst', 'subst_or_none'):
        monkeypatch.setattr(Term, name, forbidden)
    assert evaluate(term) == expected
