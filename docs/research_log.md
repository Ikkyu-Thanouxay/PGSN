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