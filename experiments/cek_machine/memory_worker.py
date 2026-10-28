"""One isolated traced-memory observation; no execution-time measurements."""
from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
import platform
import sys
import tracemalloc

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from benchmark import identity, captured
from cbv_cek import evaluate

BUILDERS = {'identity': identity, 'captured': captured}


def current(term):
    return term.fully_eval(steps=10000)


def control(term):
    # Same function-call boundary, but no evaluator execution.
    return term


EVALUATORS = {'current': current, 'cek': evaluate, 'control': control}


def observe(family, size, evaluator):
    if family not in BUILDERS or evaluator not in EVALUATORS or size < 0:
        raise ValueError('Unknown family/evaluator or negative size')
    if tracemalloc.is_tracing():
        raise RuntimeError('Worker must start without tracing enabled')
    if not gc.isenabled():
        raise RuntimeError('Automatic garbage collection must be enabled')
    # Imports, environment extraction and selection are outside tracing.
    row = dict(family=family, size=size, evaluator=evaluator, pid=os.getpid(),
               status='error', correct=None, evaluated=evaluator != 'control',
               baseline_bytes=None, peak_bytes=None, ending_bytes=None,
               peak_growth_bytes=None, end_growth_bytes=None,
               python=sys.version, executable=sys.executable,
               platform=platform.platform(), gc_enabled=True,
               gc_thresholds=list(gc.get_threshold()), recursion_limit=sys.getrecursionlimit())
    build, run = BUILDERS[family], EVALUATORS[evaluator]
    try:
        tracemalloc.start(1)
        term, expected = build(size)
        if term.is_named:
            raise ValueError('Expected a nameless input')
        gc.collect()
        baseline, _ = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        result = run(term)
        ending, peak = tracemalloc.get_traced_memory()
        # Keep input, expected and result referenced through the final read.
        tracemalloc.stop()
        row.update(baseline_bytes=baseline, peak_bytes=peak, ending_bytes=ending,
                   peak_growth_bytes=peak-baseline, end_growth_bytes=ending-baseline)
        if evaluator == 'control':
            row.update(status='ok', correct=None, result='unevaluated input',
                       control_input_preserved=result is term)
        else:
            correct = result == expected
            row.update(status='ok' if correct else 'incorrect_result',
                       correct=correct, result=repr(result), expected=repr(expected))
    except Exception as error:
        row.update(status='error', error_type=type(error).__name__, error=str(error))
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=BUILDERS, required=True)
    parser.add_argument('--size', type=int, required=True)
    parser.add_argument('--evaluator', choices=EVALUATORS, required=True)
    args = parser.parse_args()
    row = observe(args.family, args.size, args.evaluator)
    print(json.dumps(row))
    return 0 if row['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
