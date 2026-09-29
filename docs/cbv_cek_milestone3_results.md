# Milestone 3: Z recursion and Scott countdown

## Repository and checkpoint

Fetched and verified upstream/main at `1afc1909cee32dfc6c686e5e665b07fdd355b639`.
The exact starting commit is Milestone 2
`9ad56c65d7ff6297bc01a6971db1d33246fabcd8`; Milestone 1 remains at
`57b288cd78ec552cf1e1fee638ed6b3136824338`. The initial working tree was clean.
No applicable AGENTS.md files were present. Origin is `Ikkyu-Thanouxay/PGSN`;
upstream is `yamagata-lab/PGSN`, with upstream push disabled.

Final branch: `research/cbv-cek-recursion`. The single checkpoint is titled
`Add CBV-compatible recursion benchmark`. Resolve its exact commit with
`git rev-parse research/cbv-cek-recursion` (also reported in the handoff).
A commit cannot embed its own SHA; no extra metadata commit or history rewrite
is required. Milestone 1/2 code, recorded numbers, and history are preserved.

## Semantics and workload

The shared `pgsn.dsl.fix` changes from Y to Z:

```text
Y = λf. (λx. f (x x)) (λx. f (x x))
Z = λf. (λx. f (λv. x x v)) (λx. f (λv. x x v))

I      = λx. x
ZERO   = λzeroCase. λsuccCase. zeroCase
SUCC n = λzeroCase. λsuccCase. succCase n
F      = λself. λn. n I (λpred. self pred)
countdown = fix F
workload(n) = countdown (SUCC^n ZERO)
```

Strict CBV must evaluate `x x` before passing it to `f` in Y, so it unfolds
again without reaching the function body. Z passes a lambda value instead;
`λv. x x v` delays that unfolding until a recursive argument arrives. The
implementation uses the reserved internal binder `_fix_arg`. There is no
Python recursion shortcut, recursion opcode, or cyclic environment.

Size n means n successor layers / recursive predecessor traversals, plus the
zero case. The numeral is constructed as nested lambda values before execution.
At a successor, its lambda handler calls `self pred`; at zero, evaluation returns
I. Both case arguments are lambda values, so the proposed encoding works under
strict CBV without arithmetic or a conditional builtin. Every evaluated syntax
node is Variable, Abs, or App. The builder calls the real `pgsn.dsl.fix` before
`remove_name()`, rather than maintaining a private Z.

Current still uses the existing rewriting/substitution evaluator, including
unevaluated beta arguments. Changing fix does **not** make Current strict CBV.
The experimental CEK remains strict CBV with evaluated RuntimeValues in its
Environment; applying a Closure prepends the argument value. `cbv_cek.py` needed
**no modification**. No fallback to production evaluation, shift, or subst was
added.

The old conditional fixture `fix (λx.x)` could become a lambda under Z. It is now
`fix (λx.x) 0`, which forces recursion. The existing step-budget divergence test
still passes, so lazy-branch coverage has not become vacuous. Existing repeat,
fold/foldr, conditional, and recursive XML tests exercise production behavior,
not XML or Builtin support in CEK.

## Measurement method

Run from the repository root:

```sh
.venv/bin/python experiments/cek_machine/benchmark_recursion.py --sizes 1 2 5 10 20 50 100 150 200
```

Python 3.14.7, pytest 8.4.2, local macOS, 2026-09-29. The Python recursion limit
was unchanged at 1000. Start conservatively at 1–100, then probe 150 and 200; stop at
the first failing size. The final series was rerun after the initial probe.

Construction and name removal happen outside timing. Both evaluators receive
the **same nameless Term object**. Results are checked before timing and after
each run: Current must return `Abs(Variable(0))`; CEK must return a Closure whose
body is `Variable(0)`. That closure is identity regardless of captured values,
since application puts its argument at index 0. No structural equality between
Abs and Closure or general readback system is used. Tests also count recursive
applications and verify pure syntax, shared fix usage, and no CEK fallback.

The runner reuses Milestone 2's uninstrumented `perf_counter()` timing helpers:
Current uses `fully_eval(steps=10000)`; CEK uses `initial_state` and iterative
`step` until Halt. CEK total includes state initialization; there is no name
conversion for these nameless inputs. Each evaluator receives 3 warm-ups and
11 recorded runs; the table gives median milliseconds. Current runs before CEK
in each pair, as in Milestone 2. Detailed metrics run separately, before warm-up,
using unchanged `metrics.py`. Shared immutable syntax retains production's
cached free-variable bounds, so these are warm execution measurements, not
cold compilation or end-to-end front-end costs.

## Timing results

| n | Current median ms | CEK median ms |
|---:|---:|---:|
| 1 | 0.163 | 0.039 |
| 2 | 0.235 | 0.058 |
| 5 | 0.461 | 0.120 |
| 10 | 0.847 | 0.226 |
| 20 | 1.614 | 0.429 |
| 50 | 3.958 | 1.028 |
| 100 | 7.957 | 2.076 |
| 150 | 11.824 | 3.126 |
| 200 | unavailable | unavailable |

At n=200 the shared construction/name-removal stage raises `RecursionError`
**before either evaluator runs**. A traceback check locates the failure in
`free_variables()` called by `remove_name()` to form the naming context.
This is an input preparation boundary, not
evidence of a Current execution failure or a CEK execution limit. No fair
comparison exists there; no timing is invented. No recursion limit was raised,
no alternate builder bypassed the boundary, and no larger sizes were attempted.
The precise first failing n between 150 and 200 was not searched.

## Supporting counters

Definitions are unchanged from [Milestone 2](cbv_cek_milestone2_results.md).
Root reductions count successful outer progressions; beta counts lambda
applications. Shift/subst visits include pruned entries. They are operation
counts, not distinct allocated nodes or equivalent units of work.

| n | Current root = beta | shift visits | subst visits | shift pruned | subst pruned |
|---:|---:|---:|---:|---:|---:|
| 1 | 13 | 35 | 62 | 35 | 19 |
| 2 | 20 | 52 | 92 | 52 | 29 |
| 5 | 41 | 103 | 182 | 103 | 59 |
| 10 | 76 | 188 | 332 | 188 | 109 |
| 20 | 146 | 358 | 632 | 358 | 209 |
| 50 | 356 | 868 | 1532 | 868 | 509 |
| 100 | 706 | 1718 | 3032 | 1718 | 1009 |
| 150 | 1056 | 2568 | 4532 | 2568 | 1509 |

| n | CEK transitions | variable lookups | Closure applications = Environment extensions = each App frame count | max continuation depth | Builtin applications |
|---:|---:|---:|---:|---:|---:|
| 1 | 66 | 11 | 13 | 2 | 0 |
| 2 | 101 | 19 | 20 | 2 | 0 |
| 5 | 206 | 43 | 41 | 2 | 0 |
| 10 | 381 | 83 | 76 | 2 | 0 |
| 20 | 731 | 163 | 146 | 2 | 0 |
| 50 | 1781 | 403 | 356 | 2 | 0 |
| 100 | 3531 | 803 | 706 | 2 | 0 |
| 150 | 5281 | 1203 | 1056 | 2 | 0 |

“Each App frame count” means both AppFunction and AppArgument separately have
the listed count. For these inputs root/beta/Closure applications are `6 + 7n`;
CEK transitions are `31 + 35n`, and lookups `3 + 8n`. A successor adds a genuine
recursive traversal. Equal beta/application counts here do not imply equal
cost, and **one beta reduction is not one CEK transition**. Constant continuation
depth reflects tail recursion in this workload, not constant total memory.

## Verification

Commands were run in this order (no unrelated production failures observed):

- `.venv/bin/python -m pytest -q tests/test_dsl.py tests/test_conditional.py tests/test_pgsn_xml.py tests/test_expr.py tests/test_equality.py tests/test_weak_normal_form.py` — 192 passed in 0.28s.
- `.venv/bin/python -m pytest -q experiments/cek_machine/test_recursion.py` — 7 passed in 0.08s.
- `.venv/bin/python -m pytest -q experiments/cek_machine` — 40 passed in 0.08s.
- `.venv/bin/python -m pytest -q` — 574 passed, 4 deselected in 6.32s.

- `.venv/bin/python -m pytest -q -m ''` — **578 passed in 766.18s** (12m46s), including all four slow examples; no deselections or failures.

`.venv/bin/python -m py_compile experiments/cek_machine/benchmark_recursion.py experiments/cek_machine/test_recursion.py`
and `git diff --check` passed. Review confirms no CEK/metrics/Milestone 2
benchmark changes and no AGENTS.md or accidental generated artifacts.

## Interpretation and stopping point

This compares the existing Current rewriting evaluator with the experimental
strict-CBV CEK on the same controlled recursive Z-based pure-lambda workload.
CEK was faster at every successfully compared size in this local run (roughly
3.7–4.2 times). Both timings and event counts grow approximately linearly over
this small range. All Current shift calls were pruned, so the timing difference
cannot simply be described as eliminating expensive full-tree shifts.

These warm medians on one machine and one tail-recursive workload establish
neither universal CEK superiority nor full PGSN speedup. They do not attribute
all Current cost to shift/subst, establish a memory bound, benchmark cold name
removal, or imply semantic equivalence on arbitrary programs. They say nothing
about SolarWinds CEK or eu_ai_act_full CEK. Production semantics have not moved
to strict CBV.

Milestone 3 stops here: no general Builtins, List/Record, XML/GSN CEK,
recursive Environment/Closure cycles, SolarWinds CEK, eu_ai_act_full CEK,
complete evaluator replacement, or Milestone 4. Existing narrow arithmetic
support remains unchanged and is unused by this benchmark.
