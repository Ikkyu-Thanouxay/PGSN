# Baseline Evaluator Metrics

Date: 2026-07-19

Branch: `research/cek-baseline-metrics`

## 1. Research question

The current PGSN evaluator applies a lambda abstraction using shift and substitution:

```python
self.head.t
    .subst(0, self.args[0].shift(1, 0))
    .shift(-1, 0)
```

The purpose of this experiment is to answer:

> Is SolarWinds slow mainly because it performs many beta reductions, or because each beta reduction causes a large amount of shift and substitution traversal?

This experiment measures the current substitution-based evaluator before implementing an environment-based evaluator.

## 2. Added measurements

The following counters were added:

| Counter | Location | Meaning |
|---|---|---|
| Evaluation steps | `Term.fully_eval()` | Successful outer evaluation steps |
| Beta reductions | `Context.reduce_or_none()` | Applications of an `Abs` to an argument |
| Shift node visits | `Term.shift_or_none()` | Term nodes inspected by shift |
| Substitution node visits | `Term.subst_or_none()` | Term nodes inspected by substitution |

A node visit is not necessarily a visit to a unique node. If an operation repeatedly traverses the same term structure, every visit is counted. These repeated traversals are part of the evaluation cost being investigated.

The following ratios were also calculated:

```text
shift visits per beta
= shift node visits / beta reductions
```

```text
substitution visits per beta
= substitution node visits / beta reductions
```

## 3. Correctness checks

The generated documents before and after adding the counters were compared using `diff`.

| Input | Result |
|---|---|
| `gsn.xml` | Identical |
| `map_term.xml` | Identical |
| `robot.xml` | Identical |
| `cap-a.xml` | Identical |

Therefore, the added instrumentation did not change the generated documents for the four tested inputs.

The following test command was also used:

```bash
python -m pytest --ignore=tests/test_objects.py
```

Result:

```text
112 passed
```

`tests/test_objects.py` could not be collected because pytest attempted to inspect a PGSN `App` object and encountered a wrapper loop. This happened during test collection, before evaluator execution. It is recorded as a separate pre-existing compatibility issue.

## 4. Results

| Input | Eval time | Eval steps | Beta reductions | Shift visits | Subst visits | Shift/beta | Subst/beta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `gsn.xml` | 0.052063 s | 41 | 28 | 60,720 | 3,633 | 2,168.57 | 129.75 |
| `map_term.xml` | 0.042639 s | 47 | 43 | 42,535 | 4,487 | 989.19 | 104.35 |
| `robot.xml` | 0.422473 s | 85 | 69 | 570,435 | 15,838 | 8,267.17 | 229.54 |
| `cap-a.xml` | 0.319128 s | 208 | 148 | 358,841 | 18,184 | 2,424.60 | 122.86 |
| `SolarWinds.xml` | 322.338548 s | 448 | 1,426 | 483,384,975 | 1,044,353 | 338,979.65 | 732.37 |

## 5. Interpretation

### 5.1 Beta-reduction count does not explain runtime by itself

`cap-a.xml` performs 148 beta reductions, while `robot.xml` performs only 69. However, `cap-a.xml` is faster:

```text
cap-a:  0.319128 seconds
robot:  0.422473 seconds
```

`robot.xml` performs more shift traversal:

```text
cap-a:  358,841 shift visits
robot:  570,435 shift visits
```

This shows that an input with more beta reductions is not necessarily slower. The rewriting cost of each reduction is also important.

### 5.2 Rewriting work grows dramatically for SolarWinds

Compared with `robot.xml`, SolarWinds performs approximately:

```text
20.7 times more beta reductions
847 times more shift-node visits
41 times more shift visits per beta reduction
763 times more instrumented evaluation time
```

Therefore, SolarWinds is not slow only because it performs more lambda applications. The amount of term traversal caused by each application also becomes much larger.

### 5.3 Shift is the largest measured rewriting operation

For SolarWinds:

```text
Shift node visits:        483,384,975
Substitution node visits:   1,044,353
```

Shift performs approximately 463 times as many node visits as substitution.

This result agrees with the previous cProfile result, where `shift_or_none()` was the dominant evaluator function.

## 6. Conclusion

SolarWinds is slow because of both:

1. A larger number of beta reductions.
2. Much more rewriting work per beta reduction.

The second factor grows much more dramatically.

These measurements provide strong evidence that an environment-based evaluator is worth investigating. An environment-based evaluator can keep variable bindings in an environment and use closures instead of immediately rewriting the complete function body with shift and substitution.

However, these measurements do not yet prove that CEK will be faster. A CEK or CEK-style evaluator must be implemented and compared with the current evaluator using the same inputs.

## 7. Measurement limitation

The evaluation times in this report were measured while both `cProfile` and the explicit Python counters were active. The counters add runtime overhead, especially when hundreds of millions of node visits are counted.

Therefore:

- The counts and ratios are the main results of this experiment.
- The times are supporting information.
- The final substitution-versus-CEK performance comparison must also measure both evaluators with detailed counters disabled.

## 8. Next step

The next step is to define the scope of the first environment-based evaluator.

The first prototype should support:

- Variables
- Lambda abstractions
- Applications
- Constants
- Environments
- Closures
- Continuation frames

Support for PGSN-specific terms such as built-ins, lists, records, `PGSNClass`, and `PGSNObject` will be added later after the basic evaluator works correctly.
