"""One isolated research measurement; never changes production source."""
from __future__ import annotations

import argparse
import cProfile
from contextlib import contextmanager, redirect_stdout
import gc
import hashlib
import importlib.metadata
import importlib.util
import io
import json
from pathlib import Path
import platform
import pstats
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

# Explicitly inspected entries only. No automatic discovery/import of Python files.
PYTHON_ENTRIES = {
    'examples/cli.py': 'main',
    'examples/gsn.py': 'main',
    'examples/map_term.py': 'main',
    'examples/SolarWinds.py': 'solarwinds',
    'examples/cap-a.py': 'cap_a_term',
}
TIMINGS = ('load_seconds', 'eval_seconds', 'gsn_seconds', 'output_seconds',
           'worker_total_seconds', 'process_wall_seconds')


def environment():
    clock = time.get_clock_info('perf_counter')
    return dict(python_version=sys.version, executable=sys.executable,
                platform=platform.platform(), machine=platform.machine(),
                package_version=importlib.metadata.version('pgsn'),
                perf_counter=vars(clock), gc_enabled=gc.isenabled(),
                gc_thresholds=gc.get_threshold(), recursion_limit=sys.getrecursionlimit())


def load_term(path):
    from pgsn.pgsn_term import Term
    from pgsn.pgsn_xml import compile_pgsn
    if path.endswith('.xml'):
        import xml.etree.ElementTree as ET
        if ET.parse(ROOT / path).getroot().tag != 'PGSN':
            raise ValueError('XML modules are not standalone programs')
        return compile_pgsn(ROOT / path)
    if path not in PYTHON_ENTRIES:
        raise ValueError('Python input is not explicitly registered as safe')
    spec = importlib.util.spec_from_file_location('research_example', ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    term = vars(module)[PYTHON_ENTRIES[path]]
    if not isinstance(term, Term):
        raise TypeError('Registered entry is not a Term')
    return term


@contextmanager
def counters():
    """Same visit/beta/pruning definitions as CEK metrics; restore on every exit."""
    from pgsn.pgsn_term import Term, Context, Abs
    counts = dict(root_reductions=0, beta_reductions=0, shift_visits=0,
                  subst_visits=0, shift_pruned=0, subst_pruned=0)
    originals = Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none

    def shift(self, num, cutoff):
        counts['shift_visits'] += 1
        counts['shift_pruned'] += self.free_bound() <= cutoff
        return originals[0](self, num, cutoff)

    def subst(self, variable, term):
        counts['subst_visits'] += 1
        counts['subst_pruned'] += self.free_bound() <= variable
        return originals[1](self, variable, term)

    def reduce(self):
        counts['beta_reductions'] += isinstance(self.head, Abs) and bool(self.args)
        return originals[2](self)

    Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none = shift, subst, reduce
    try:
        yield counts
    finally:
        Term.shift_or_none, Term.subst_or_none, Context.reduce_or_none = originals


def counted_eval(term, steps):
    # As in CEK metrics, initial name removal is outside the counter wrappers.
    current = term.remove_name() if term.is_named else term
    with counters() as counts:
        for _ in range(steps):
            reduced = current.eval_or_none()
            if reduced is None:
                return current, counts
            counts['root_reductions'] += 1
            current = reduced
    raise RuntimeError('Counter pass exceeded evaluation step budget')


def profile_report(profiler):
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, line, name), (primitive, total, self_s, cumulative_s, _) in stats.stats.items():
        rows.append(dict(file=filename, line=line, function=name,
                         primitive_calls=primitive, total_calls=total,
                         self_seconds=self_s, cumulative_seconds=cumulative_s))
    text = io.StringIO()
    for sort in ('cumulative', 'tottime'):
        pstats.Stats(profiler, stream=text).sort_stats(sort).print_stats(40)
    return dict(top_cumulative=sorted(rows, key=lambda r: r['cumulative_seconds'], reverse=True)[:40],
                top_self=sorted(rows, key=lambda r: r['self_seconds'], reverse=True)[:40],
                total_calls=stats.total_calls, primitive_calls=stats.prim_calls,
                total_self_seconds=stats.total_tt, readable_report=text.getvalue())


def run(path, mode='clean', steps=1_000_000):
    # Standard imports above and interpreter startup excluded from worker_total.
    # PGSN imports/initialization and all pipeline/hash work below are included.
    start = time.perf_counter()
    result = dict(path=path, mode=mode, status='error', step_budget=steps)
    captured = io.StringIO()
    try:
        with redirect_stdout(captured):
            t0 = time.perf_counter()
            term = load_term(path)
            result['load_seconds'] = time.perf_counter() - t0
            from pgsn.gsn import gsn_tree
            t0 = time.perf_counter()
            if mode == 'clean':
                value = term.fully_eval(steps=steps)
                result['eval_seconds'] = time.perf_counter() - t0
            elif mode == 'counters':
                value, result['counts'] = counted_eval(term, steps)
            elif mode == 'profile':
                profiler = cProfile.Profile()
                value = profiler.runcall(term.fully_eval, steps=steps)
                result['profile'] = profile_report(profiler)
            else:
                raise ValueError('Unknown mode')
            t0 = time.perf_counter()
            tree = gsn_tree(value)
            result['gsn_seconds'] = time.perf_counter() - t0
            t0 = time.perf_counter()
            document = tree.show(stdout=False, sorting=False, idhidden=True,
                                 line_type='ascii-ex')
            result['output_seconds'] = time.perf_counter() - t0
            data = document.encode('utf-8')
            result.update(status='ok', output_sha256=hashlib.sha256(data).hexdigest(),
                          output_bytes=len(data), output_type='treelib Tree.show UTF-8',
                          serialization='stdout=False; sorting=False; idhidden=True; line_type=ascii-ex')
        if captured.getvalue():
            raise RuntimeError('Unexpected stdout during input pipeline: ' + captured.getvalue()[:1000])
    except Exception:
        result.update(status='error', error=traceback.format_exc())
    result['worker_total_seconds'] = time.perf_counter() - start
    if mode != 'clean':
        # Diagnostic elapsed times never occupy clean timing columns.
        for field in TIMINGS:
            if field in result:
                result['diagnostic_' + field] = result.pop(field)
    result['environment'] = environment()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True)
    parser.add_argument('--mode', choices=['clean', 'counters', 'profile'], required=True)
    parser.add_argument('--steps', type=int, default=1_000_000)
    args = parser.parse_args()
    print(json.dumps(run(args.path, args.mode, args.steps), ensure_ascii=False))
