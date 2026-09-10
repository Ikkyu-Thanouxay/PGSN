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
