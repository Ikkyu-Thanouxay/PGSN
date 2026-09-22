"""Deterministic research-counter checks."""
from cbv_cek import evaluate
from metrics import measure_cek, measure_current
from pgsn.pgsn_term import Abs, App, Context, Integer, Plus, Term, Variable


def test_identity_counters_and_restoration():
    term = App.term(Abs.nameless(v=None, t=Variable.nameless(num=0)),
                    Integer.nameless(value=7))
    original = (Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none)
    current, production = measure_current(term)
    cek, machine = measure_cek(term)
    assert current == cek == evaluate(term) == Integer.nameless(value=7)
    assert production.root_reductions == production.beta_reductions == 1
    assert production.shift_visits > 0 and production.subst_visits > 0
    assert machine.transitions > 0 and machine.lookups == 1
    assert machine.closure_applications == machine.environment_extensions == 1
    assert machine.max_continuation_depth > 0
    assert machine.app_function_frames == machine.app_argument_frames == 1
    assert original == (Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none)


def test_builtin_and_exception_restoration():
    term = App.term(App.term(Plus.nameless(), Integer.nameless(value=1)),
                    Integer.nameless(value=2))
    current, _ = measure_current(term)
    cek, counters = measure_cek(term)
    assert current == cek == Integer.nameless(value=3)
    assert counters.builtin_applications == 1
    original = (Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none)
    try:
        measure_current(term, steps=0)
    except RuntimeError:
        pass
    assert original == (Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none)
