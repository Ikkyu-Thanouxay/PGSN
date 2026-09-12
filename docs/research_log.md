# PGSN Research Log

## 2026-06-25: Profiler investigation

### Task
Add profiling support to PGSN and identify slow parts.

### Result
XML loading and tree output were not the main bottleneck.

The main bottleneck was evaluation, especially:
- fully_eval
- shift_or_none
- subst_or_none
- reduce_or_none

### Interpretation
PGSN terms are lambda-calculus-like. Current evaluation uses substitution.
Substitution causes many recursive traversals and many shift operations.

### Next task from professor
Study CEK / CESK machines and consider whether PGSN can be evaluated faster using an abstract machine or bytecode.

## CEK mini experiment checkpoint

### Purpose

Before modifying the real PGSN evaluator, we created a small experiment in:

`experiments/cek_machine/mini_cek.py`

The goal is to compare:

- substitution-based lambda evaluation
- CEK-style environment-based evaluation

### Why this matters

The profiler showed that PGSN evaluation is slow around repeated substitution and shifting.
A CEK-style evaluator may reduce this by using environments instead of directly substituting arguments into function bodies.

### What happened

A first mini evaluator was added.

During the first run, the nested lambda example failed because the substitution evaluator treated a lambda abstraction as not being a value.

That was wrong. In lambda calculus, a lambda abstraction is a function value.

The fix was:

- allow `Abs` to be returned as a value in `eval_subst`
- evaluate the function side of an application before applying it
- then substitute into the function body

### Current status

The mini examples now run successfully:

- identity function
- nested lambda
- duplicated variable with addition

Both the substitution evaluator and CEK evaluator return the same results.

### Git note

Commit `c6f8f49` is named `Fix mini CEK substitution evaluator`, but it also includes most of the first mini CEK implementation because the broken version was never committed separately.

## Test status

Command:

`python -m pytest --ignore=tests/test_objects.py`

Result:

- 112 tests passed.
- `tests/test_objects.py` could not be collected because pytest attempted
  to inspect a PGSN `App` object and encountered a wrapper loop.
- This happens during test collection, before evaluator execution.
- It is treated as a separate pre-existing compatibility issue and is
  outside the baseline-metrics change.

## 2026-09-10: Environment evaluator scaling and Builtin checkpoint

### Purpose

Evaluate whether environment-based evaluation is promising for reducing
the repeated `shift` / `subst` traversal observed in the current PGSN evaluator.

### Correctness

The environment evaluator was compared with the current evaluator.

13 comparison tests now pass, including:

- basic lambda application
- captured variables
- delayed and unused arguments
- a deep nested-lambda stress case
- arithmetic Builtins: `plus`, `minus`, `times`, and `div`
- Builtin arguments obtained through an environment
- a Builtin passed through the environment as a function

The tested expressions produced the same final results in both evaluators.

### Scaling result

A synthetic captured-variable expression was tested at depths:

- 10
- 25
- 50
- 100
- 200

For this workload, `shift` and `subst` node visits in the current evaluator
grew approximately quadratically with nesting depth.

The environment evaluator instead used closures, delayed arguments, and
environment lookup without rewriting the lambda body during beta reduction.

Repeated timing measurements showed that the performance difference became
larger as nesting depth increased.

This result applies only to the tested synthetic lambda workload and does
not establish the performance of full PGSN programs.

### Arithmetic Builtin extension

The prototype was extended with `BuiltinClosure`.

The same mechanism supports:

- `plus`
- `minus`
- `times`
- `div`

It also works when an arithmetic argument comes from an environment and
when the Builtin itself is passed as a function.

### Current conclusion

Environment-based evaluation appears promising for reducing the
substitution/shift bottleneck identified in the current evaluator.

The prototype is still incomplete. General Builtins, lists, records,
PGSN classes/objects, real XML workloads, and an explicit continuation
structure remain future work.

Detailed Day 4 measurements:

`experiments/cek_machine/day4_results.md`

Reproducible benchmark:

`experiments/cek_machine/benchmark_pgsn_env_eval.py`

Raw final benchmark output:

`experiments/cek_machine/day4_benchmark_output.txt`

## 2026-09-12: Python example milestone — baseline and plan

- Goal: evaluate the existing `examples/cli.py` `main` end-to-end and compare
  the complete result with the current evaluator; stop at the Python milestone.
- Starting commit: `c693a8f10e6d765684e0b64ad5524fbe580eb2e7`.
  Branch: `research/env-evaluator-py-support`; working tree initially clean.
- Inspected: AGENTS.md, prototype, comparison tests, benchmark implementation
  (not executed), this log, recent git history, evaluator Term/Context/Builtin
  implementations, DSL keyword/class constructors, GSN constructors, existing
  Python examples, and record/object tests.
- Baseline: `.venv/bin/python -m pytest experiments/cek_machine/test_pgsn_env_eval.py`
  **13 passed in 0.08s**; `.venv/bin/python -m pytest` **352 passed in 0.71s**.
  `python` was absent and system `python3` lacked pytest; use the existing venv.
  The old collection problem in test_objects.py does not reproduce.
- Selection: `examples/cli.py` is the smallest standalone GSN entry-point
  example: a goal, strategy, two child goals and evidence. `gsn.py`/`secure.py`
  duplicate this graph with extra imports/display; custom_goal adds a custom
  class, map_term adds mapping, and other examples add templates, external
  inputs or rendering. No example source will be rewritten or pre-evaluated.
- Exact initial syntax inventory: App 101, Variable 84, String 83, Record 60,
  List 41, Abs 34, DefineClass 24, PGSNClass 9, OverwriteRecord 6.
  Current evaluator returns PGSNObject; prototype first fails on DefineClass.
  Blockers: Record construction/projection, List values, PGSNClass values and
  application, PGSNObject values, DefineClass and OverwriteRecord. PGSNObject
  is generated at runtime. No other Builtin family is needed.
- Semantic finding: Context checks Builtin applicability before reducing the
  head or arguments. Record projection and overwrite can discard erroneous
  fields. Container normalization advances each child one reduction per pass;
  fully evaluating children in sequence can change which error occurs first.
  Invalid applications may remain stuck Terms in the current evaluator,
  whereas the prototype raises TypeError. Preserve stuck results for the new
  path; do not silently manufacture successful values.
- Plan: add an environment-backed structured evaluation path, with suspended
  children and one-step reduction matching Context/container order. Preserve
  delayed beta arguments using environments, reuse only the selected Builtin
  predicates/operations, and materialize ordinary Terms at the result boundary.
  Do not delegate evaluation to fully_eval, eval_or_none, shift or subst.
  Compare projection/overwrite laziness, captured variables, error order,
  class defaults/overrides and complete GSN output. Keep the existing scalar
  path/tests as a baseline. Commit stable related support with tests, then add
  the unchanged Python entry-point integration check and reproduction command.
- Limits: this establishes correctness on the selected program and focused
  cases, not general PGSN support or real-program speedups. No benchmarks,
  explicit K implementation, or XML feature work is planned.

### Structured support checkpoint

- Plan checkpoint: `4d5e75b` (pushed). Added
  `experiments/cek_machine/pgsn_env_structured.py`, dispatched from eval_env when
  the input syntax contains the selected structured families. Kept the original
  scalar evaluator and its metrics path intact. Internal immutable Term slots
  retain environments; beta reduction extends the environment without rewriting
  the body. A separate reduction loop follows Context order and advances all
  container children one step per pass. Shape inspection resolves bindings but
  does not reduce applications; selected existing Builtin predicates/operations
  retain slots through record merging and object construction. Final materialization
  returns ordinary Terms. No reference reduction/shift/substitution is called.
- Added 16 comparisons (29 focused tests total): full structural equality,
  lazy record projection/overwrite/list indexing, needed division errors,
  captures/shadowing, unused arguments, class inheritance/defaults/override,
  object projection, stuck invalid applications, and primitive event traces.
- Observed subtle reference behavior: an overridden erroneous class default is
  skipped by immediate object projection but still raises when normalizing the
  entire object, because the object retains its class. Both cases now match.
  Round-robin error test confirms the second field's division error occurs
  before the first field's delayed addition, matching the current evaluator.
- Tests: focused **29 passed in 0.08s**; full **368 passed in 0.70s**;
  `git diff --check` passed. No failed implementation/test attempts so far.
- Limits: the new path deliberately rejects escaping lambdas in structured
  normal forms (including function-valued fields/methods), free variables and
  unselected Terms/Builtins. General higher-order structured data is not claimed.
  The scalar path retains its pre-existing closure return convention and
  TypeError behavior for invalid applications; the structured path preserves
  reference stuck Terms. This is a bounded extension, not universal parity.
  Structured slots/shape traversals are not included in the old prototype
  metrics, and shape inspection can traverse data repeatedly. No performance
  conclusions follow from this implementation.
- Next: run the unchanged selected Python program through both evaluators,
  compare complete Terms, Python values and GSN tree content, and verify no
  reference evaluator traversal is used. Record the support commit SHA in the
  next checkpoint. No production evaluator or existing example was modified.
