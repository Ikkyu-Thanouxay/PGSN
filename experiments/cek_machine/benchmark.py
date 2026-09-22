"""Run controlled successful-subset measurements from the repository root."""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from statistics import median
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cbv_cek import evaluate, initial_state, step
from metrics import measure_cek, measure_current
from pgsn.pgsn_term import Abs, App, Integer, Plus, Variable


def integer(n):
    return Integer.nameless(value=n)


def identity(n):
    ident = Abs.nameless(v=None, t=Variable.nameless(num=0))
    term = integer(7)
    for _ in range(n):
        term = App.term(ident, term)
    return term, integer(7)


def captured(n):
    # Each layer applies a closure that returns its captured outer value.
    outer = Variable.nameless(num=1)
    keep_outer = Abs.nameless(v=None, t=outer)
    term = integer(7)
    for _ in range(n):
        term = App.term(App.term(Abs.nameless(v=None, t=keep_outer), term), integer(0))
    return term, integer(7)


def arithmetic(n):
    plus = Plus.nameless()
    term = integer(0)
    for _ in range(n):
        term = App.term(App.term(plus, term), integer(1))
    return term, integer(n)


def time_current(term):
    start = perf_counter()
    result = term.fully_eval(steps=10000)
    return result, perf_counter() - start


def time_cek(term):
    start = perf_counter()
    state = initial_state(term)
    removed = perf_counter()
    while not state.halted:
        state = step(state)
    ended = perf_counter()
    return state.control, ended - start, removed - start, ended - removed


def run_case(name, size, build):
    try:
        term, expected = build(size)
        assert term.fully_eval(steps=10000) == expected
        assert evaluate(term) == expected
        current_result, current = measure_current(term)
        cek_result, cek = measure_cek(term)
        assert current_result == cek_result == expected
        for _ in range(3):
            assert time_current(term)[0] == expected
            assert time_cek(term)[0] == expected
        current_times, cek_times, remove_times, loop_times = [], [], [], []
        for _ in range(11):
            result, duration = time_current(term)
            assert result == expected
            current_times.append(duration)
            result, total, remove, loop = time_cek(term)
            assert result == expected
            cek_times.append(total)
            remove_times.append(remove)
            loop_times.append(loop)
        return dict(family=name, size=size, status='ok', current_ms=median(current_times)*1000,
                    cek_total_ms=median(cek_times)*1000, cek_remove_ms=median(remove_times)*1000,
                    cek_loop_ms=median(loop_times)*1000, root=current.root_reductions,
                    beta=current.beta_reductions, shift=current.shift_visits,
                    subst=current.subst_visits, shift_pruned=current.shift_pruned,
                    subst_pruned=current.subst_pruned, transitions=cek.transitions,
                    lookups=cek.lookups, closures=cek.closure_applications,
                    builtins=cek.builtin_applications, app_function=cek.app_function_frames,
                    app_argument=cek.app_argument_frames, env_extensions=cek.environment_extensions,
                    max_depth=cek.max_continuation_depth)
    except (RecursionError, RuntimeError) as error:
        return dict(family=name, size=size, status=f'{type(error).__name__}: {error}')


def main():
    rows = []
    for name, build in [('identity', identity), ('captured', captured), ('arithmetic', arithmetic)]:
        for size in (10, 100, 200, 500, 1000, 2000):
            row = run_case(name, size, build)
            rows.append(row)
            print(name, size, row['status'], flush=True)
    columns = ['family', 'size', 'status', 'current_ms', 'cek_total_ms', 'cek_remove_ms',
               'cek_loop_ms', 'root', 'beta', 'shift', 'subst', 'shift_pruned',
               'subst_pruned', 'transitions', 'lookups', 'closures', 'builtins',
               'app_function', 'app_argument', 'env_extensions', 'max_depth']
    writer = csv.DictWriter(sys.stdout, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({key: f'{value:.3f}' if isinstance(value, float) else value
                         for key, value in row.items()})


if __name__ == '__main__':
    main()
