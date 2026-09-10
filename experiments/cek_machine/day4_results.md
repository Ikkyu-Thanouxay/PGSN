# Day 4 Environment Evaluator Results

## Research question

Can an environment-based evaluator reduce the large amount of
`shift` / `subst` tree traversal performed by the current PGSN evaluator,
while preserving the current evaluation behavior?

## Prototype

Current prototype:

- Environment
- Closure
- DelayedArgument
- Control term is explicit as `term`
- Environment is explicit as `env`
- Continuation is still implicit in the Python call stack
- No explicit K structure yet

The prototype avoids beta substitution of the function body.
Arguments are stored as `DelayedArgument` values and evaluated when needed.

---

## Correctness and operation-count tests

All 7 comparison tests produced the same final result in both evaluators.

| Test | Beta | Shift visits | Subst visits | Env lookups | Closures | Delayed created | Delayed evaluated |
|---|---:|---:|---:|---:|---:|---:|---:|
| Identity | 1 | 2 | 1 | 1 | 1 | 1 | 1 |
| Constant function | 1 | 2 | 1 | 0 | 1 | 1 | 0 |
| Captured variable | 2 | 6 | 3 | 1 | 2 | 2 | 1 |
| Function argument | 2 | 8 | 4 | 2 | 2 | 2 | 2 |
| Unused argument | 1 | 4 | 1 | 0 | 1 | 1 | 0 |
| Used delayed argument | 2 | 10 | 2 | 2 | 2 | 2 | 2 |
| Deep captured variable (depth=100) | 101 | 10302 | 5151 | 1 | 101 | 101 | 1 |

### Evaluation-order observations

Unused argument:

`(λx. 1) (1 2) -> 1`

- Delayed arguments created: 1
- Delayed arguments evaluated: 0
- Environment lookups: 0

The unused argument is stored but not evaluated.

Used delayed argument:

`(λx. x) ((λz. z) 7) -> 7`

- Delayed arguments created: 2
- Delayed arguments evaluated: 2
- Environment lookups: 2

The argument is evaluated later when it is needed.

---

## Timing benchmark

The benchmark disables environment metrics while measuring time.

Small tests:

- 1000 evaluations per batch
- 7 batches
- Reported value is the median of the 7 per-batch average times

Deep stress test:

- 100 evaluations per batch
- 7 batches

| Test | Current evaluator | Environment evaluator | Current / Environment |
|---|---:|---:|---:|
| Identity | 0.010268 ms | 0.010685 ms | 0.96x |
| Constant function | 0.010506 ms | 0.009950 ms | 1.06x |
| Captured variable | 0.024091 ms | 0.018496 ms | 1.30x |
| Function argument | 0.024102 ms | 0.019019 ms | 1.27x |
| Unused argument | 0.015050 ms | 0.014618 ms | 1.03x |
| Used delayed argument | 0.021629 ms | 0.018390 ms | 1.18x |
| Deep captured variable (depth=100) | 14.881305 ms | 0.915370 ms | 16.26x |

For very small expressions, the two evaluators have similar execution time.
The environment representation itself has some overhead.

The advantage becomes much larger for a substitution-heavy nested expression.

---

## Scaling experiment

Synthetic expression:

`(λx. λy0. λy1. ... λyn. x) 5 0 0 ... 0`

The nesting depth was increased while preserving the same basic behavior.

### Timing

| Depth | Current evaluator | Environment evaluator | Current / Environment |
|---:|---:|---:|---:|
| 10 | 0.257762 ms | 0.087057 ms | 2.96x |
| 25 | 1.131585 ms | 0.198902 ms | 5.69x |
| 50 | 3.902940 ms | 0.387853 ms | 10.06x |
| 100 | 14.715012 ms | 0.764690 ms | 19.24x |
| 200 | 58.769072 ms | 1.552054 ms | 37.87x |

### Operation counts

| Depth | Beta | Shift visits | Subst visits | Env lookups | Closures | Delayed created | Delayed evaluated |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 11 | 132 | 66 | 1 | 11 | 11 | 1 |
| 25 | 26 | 702 | 351 | 1 | 26 | 26 | 1 |
| 50 | 51 | 2652 | 1326 | 1 | 51 | 51 | 1 |
| 100 | 101 | 10302 | 5151 | 1 | 101 | 101 | 1 |
| 200 | 201 | 40602 | 20301 | 1 | 201 | 201 | 1 |

For depth `d`, the observed pattern is:

- beta reductions = d + 1
- closures created = d + 1
- delayed arguments created = d + 1
- subst visits = (d + 1)(d + 2) / 2
- shift visits = (d + 1)(d + 2)
- environment lookups = 1
- delayed arguments evaluated = 1

For this synthetic workload, the measurements suggest approximately
quadratic growth of shift/substitution traversal in the current evaluator,
while the main environment bookkeeping grows approximately linearly.

This statement applies only to this synthetic nested-lambda workload,
not to all PGSN programs.

---

## Current conclusion

The environment-based prototype preserved the same result for all tested
lambda-calculus cases and preserved the tested delayed-argument behavior.

For small expressions, execution time was similar to the current evaluator.

For deeply nested substitution-heavy expressions, the current evaluator
performed a rapidly increasing number of shift/substitution node visits,
while the environment-based prototype avoided rewriting the function body.

This provides evidence that environment-based evaluation is promising for
reducing the substitution/shift bottleneck previously observed in PGSN.

The result does NOT mean that full PGSN is currently 16x or 38x faster.
The prototype only supports a limited subset of PGSN.

---

## Current limitations

Currently supported:

- Integer
- String
- Boolean
- Constant
- Variable
- Abs
- App
- Environment
- Closure
- DelayedArgument

Arithmetic Builtin support added:

- plus
- minus
- times
- div
- partial Builtin application through BuiltinClosure
- Builtin arguments can come from the environment
- a Builtin can itself be passed through the environment as a function

Not yet supported by the prototype:

- general PGSN Builtins beyond the tested arithmetic operators
- List
- Record
- PGSNClass
- PGSNObject
- full real PGSN documents

There is also no explicit continuation structure yet.
The role of K is currently handled implicitly by Python recursion.

---

## Arithmetic Builtin extension

The environment evaluator was extended with a generic `BuiltinClosure`
mechanism for the four integer arithmetic operators:

- plus
- minus
- times
- div

A BuiltinClosure stores a Builtin together with arguments collected so far.
The operation is applied only after the required number of arguments has
been collected.

### Direct arithmetic tests

| Expression | Expected | Current | Environment | Same result |
|---|---:|---:|---:|---|
| plus 7 3 | 10 | 10 | 10 | YES |
| minus 7 3 | 4 | 4 | 4 | YES |
| times 7 3 | 21 | 21 | 21 | YES |
| div 7 3 | 2 | 2 | 2 | YES |

For each direct arithmetic test:

Current evaluator:

- beta reductions: 0
- shift node visits: 0
- subst node visits: 0

Environment evaluator:

- environment lookups: 0
- closures created: 0
- delayed arguments created: 2
- delayed arguments evaluated: 2

These operations are Builtin applications rather than lambda beta
reductions, so the current evaluator does not perform beta/shift/subst
work for these simple direct cases.

### Builtin and environment integration tests

#### Argument obtained from the environment

Expression:

`(lambda x. plus x 3) 7 -> 10`

Both evaluators returned 10.

Current evaluator:

- beta reductions: 1
- shift node visits: 6
- subst node visits: 5

Environment evaluator:

- environment lookups: 1
- closures created: 1
- delayed arguments created: 3
- delayed arguments evaluated: 3

#### Builtin passed as a function

Expression:

`(lambda f. f 7 3) plus -> 10`

Both evaluators returned 10.

Current evaluator:

- beta reductions: 1
- shift node visits: 6
- subst node visits: 5

Environment evaluator:

- environment lookups: 1
- closures created: 1
- delayed arguments created: 3
- delayed arguments evaluated: 3

These tests show that the arithmetic Builtin mechanism is not limited to
literal expressions such as `plus 7 3`. It also works when values and the
Builtin itself pass through the environment.

---

## Day 4 conclusion

The main internship investigation now has two results:

1. The environment-based lambda evaluator preserves the tested evaluation
   behavior while avoiding repeated beta substitution of function bodies.

2. The prototype can be extended beyond the basic lambda subset. The four
   arithmetic Builtins were supported through one shared BuiltinClosure
   mechanism and worked correctly with environment-bound values.

The scaling experiment remains synthetic and the prototype is not yet a
complete replacement for the current PGSN evaluator. Real PGSN structures,
additional Builtins, and full XML workloads remain future work.
