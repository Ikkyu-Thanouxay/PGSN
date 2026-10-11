"""Milestone 3: the same Z-based Scott countdown on Current and strict CBV CEK."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from statistics import mean, median, quantiles, stdev
import json
import sys

from pgsn import dsl
from pgsn.pgsn_term import Abs, Variable
from cbv_cek import Closure
from benchmark import time_current, time_cek
from metrics import measure_current, measure_cek


def countdown(size):
    """Build named Scott syntax with the real DSL fix; remove names before timing."""
    if size < 0:
        raise ValueError('size must be nonnegative')
    x, zero, succ, self, n, pred = map(
        dsl.variable, ('x', 'zeroCase', 'succCase', 'self', 'n', 'pred'))
    identity = dsl.lambda_abs(x, x)
    numeral = dsl.lambda_abs_vars((zero, succ), zero)
    for _ in range(size):
        numeral = dsl.lambda_abs_vars((zero, succ), succ(numeral))
    maker = dsl.lambda_abs_vars(
        (self, n), n(identity)(dsl.lambda_abs(pred, self(pred))))
    return dsl.fix(maker)(numeral).remove_name()


def check_current(result):
    assert isinstance(result, Abs)
    assert result.t == Variable.nameless(num=0)


def check_cek(result):
    # A closure with body index 0 is identity regardless of its captured env:
    # applying it prepends the argument, and index 0 returns that argument.
    assert isinstance(result, Closure)
    assert result.body == Variable.nameless(num=0)


def run_case(size, warmups=3, runs=11):
    if warmups < 0 or runs < 2:
        raise ValueError("warmups must be nonnegative and runs must be at least 2")
    stage = 'construction/name removal'
    try:
        term = countdown(size)
        stage = 'Current verification'
        check_current(time_current(term)[0])
        stage = 'CEK verification'
        check_cek(time_cek(term)[0])
        stage = 'Current metrics'
        result, current = measure_current(term)
        check_current(result)
        stage = 'CEK metrics'
        result, cek = measure_cek(term)
        check_cek(result)
        assert cek.builtin_applications == 0
        stage = 'warm-up'
        for _ in range(warmups):
            check_current(time_current(term)[0])
            check_cek(time_cek(term)[0])
        current_times, cek_times = [], []
        stage = 'recorded evaluation'
        for _ in range(runs):
            result, duration = time_current(term)
            check_current(result)
            current_times.append(duration)
            result, duration, _, _ = time_cek(term)
            check_cek(result)
            cek_times.append(duration)
        counters = asdict(current) | asdict(cek)
        del counters['remove_name_seconds'], counters['loop_seconds']
        return dict(size=size, status='ok', current_ms=median(current_times)*1000,
                    cek_ms=median(cek_times)*1000,
                    **timing_statistics('current', current_times),
                    **timing_statistics('cek', cek_times), **counters)
    except RecursionError:
        # No substitute timing, recursion-limit change, or larger probe.
        return dict(size=size, status=f'RecursionError during {stage}')


def timing_statistics(prefix, seconds):
    samples = [value * 1000 for value in seconds]
    q1, _, q3 = quantiles(samples, n=4, method='inclusive')
    return {f'{prefix}_samples_ms': json.dumps(samples),
            f'{prefix}_mean_ms': mean(samples),
            f'{prefix}_stdev_ms': stdev(samples),
            f'{prefix}_iqr_ms': q3 - q1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes', nargs='+', type=int, default=[1, 2, 5, 10, 20, 50, 100])
    parser.add_argument('--warmups', type=int, default=3)
    parser.add_argument('--runs', type=int, default=11)
    args = parser.parse_args()
    if args.warmups < 0 or args.runs < 2:
        parser.error('--warmups must be nonnegative and --runs must be at least 2')
    rows = []
    for size in args.sizes:
        row = run_case(size, args.warmups, args.runs)
        rows.append(row)
        print(f"n={size}: {row['status']}", file=sys.stderr, flush=True)
        if row['status'] != 'ok':
            break
    columns = list(dict.fromkeys(key for row in rows for key in row))
    writer = csv.DictWriter(sys.stdout, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)


if __name__ == '__main__':
    main()
