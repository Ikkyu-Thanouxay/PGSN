"""Research-only counters for the current evaluator and minimal CEK."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter

from pgsn.pgsn_term import Abs, Context, Term
from cbv_cek import (AppArgument, AppFunction, Closure, Halt, PartialBuiltin,
                     State, initial_state, is_value, step)
from pgsn.pgsn_term import App, Variable


@dataclass
class CEKMetrics:
    remove_name_seconds: float = 0.0
    loop_seconds: float = 0.0
    transitions: int = 0
    lookups: int = 0
    closure_applications: int = 0
    builtin_applications: int = 0
    app_function_frames: int = 0
    app_argument_frames: int = 0
    environment_extensions: int = 0
    max_continuation_depth: int = 0

    @property
    def total_seconds(self):
        return self.remove_name_seconds + self.loop_seconds


@dataclass
class CurrentMetrics:
    root_reductions: int = 0
    beta_reductions: int = 0
    shift_visits: int = 0
    subst_visits: int = 0
    shift_pruned: int = 0
    subst_pruned: int = 0


def _depth(continuation):
    depth = 0
    while not isinstance(continuation, Halt):
        depth += 1
        continuation = continuation.continuation
    return depth


def measure_cek(term):
    metrics = CEKMetrics()
    start = perf_counter()
    state = initial_state(term)
    metrics.remove_name_seconds = perf_counter() - start
    start = perf_counter()
    while not state.halted:
        control, continuation = state.control, state.continuation
        metrics.max_continuation_depth = max(metrics.max_continuation_depth,
                                             _depth(continuation))
        if isinstance(control, Variable):
            metrics.lookups += 1
        elif isinstance(control, App):
            metrics.app_function_frames += 1
        elif is_value(control) and isinstance(continuation, AppFunction):
            metrics.app_argument_frames += 1
        elif is_value(control) and isinstance(continuation, AppArgument):
            if isinstance(continuation.function, Closure):
                metrics.closure_applications += 1
                metrics.environment_extensions += 1
            elif isinstance(continuation.function, PartialBuiltin):
                if len(continuation.function.args) + 1 == continuation.function.builtin.arity:
                    metrics.builtin_applications += 1
        state = step(state)
        metrics.transitions += 1
    metrics.max_continuation_depth = max(metrics.max_continuation_depth,
                                         _depth(state.continuation))
    metrics.loop_seconds = perf_counter() - start
    return state.control, metrics


@contextmanager
def _instrument_current(metrics):
    original_shift = Term.shift_or_none
    original_subst = Term.subst_or_none
    original_reduce = Context.reduce_or_none

    def shift(self, num, cutoff):
        metrics.shift_visits += 1
        if self.free_bound() <= cutoff:
            metrics.shift_pruned += 1
        return original_shift(self, num, cutoff)

    def subst(self, variable, term):
        metrics.subst_visits += 1
        if self.free_bound() <= variable:
            metrics.subst_pruned += 1
        return original_subst(self, variable, term)

    def reduce(self):
        if isinstance(self.head, Abs) and self.args:
            metrics.beta_reductions += 1
        return original_reduce(self)

    Term.shift_or_none = shift
    Term.subst_or_none = subst
    Context.reduce_or_none = reduce
    try:
        yield
    finally:
        Term.shift_or_none = original_shift
        Term.subst_or_none = original_subst
        Context.reduce_or_none = original_reduce


def measure_current(term, steps=10000):
    """Run the same outer progression as fully_eval with research wrappers."""
    metrics = CurrentMetrics()
    current = term.remove_name() if term.is_named else term
    with _instrument_current(metrics):
        for _ in range(steps):
            reduced = current.eval_or_none()
            if reduced is None:
                return current, metrics
            metrics.root_reductions += 1
            current = reduced
    raise RuntimeError('Current evaluator step budget exceeded in metrics pass')
