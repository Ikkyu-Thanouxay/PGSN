# Scope of the PGSN Environment-Based Evaluator

Date: 2026-07-19
Updated: 2026-09-07 (Change Vision internship Day 1)

Branch: `research/cek-baseline-metrics`

## 1. Purpose

The baseline measurement showed that the current substitution-based evaluator performs a very large amount of term rewriting.

For SolarWinds:

```text
Beta reductions:       1,426
Shift node visits:     483,384,975
Substitution visits:   1,044,353
Shift visits per beta: 338,979.65
```

The purpose of the new evaluator is to investigate whether environments and closures can avoid repeated shift and substitution traversal.

The first implementation will be a small environment-based prototype. It will not support every PGSN feature immediately.

## 2. Current evaluator behavior

The current evaluator reduces an application through `Context.reduce_or_none()`.

Its evaluation order is:

1. If the head is an `Abs` and an argument exists, apply the abstraction.
2. If the head is a `Builtin` and it has applicable arguments, apply the built-in.
3. Otherwise, try to reduce the head.
4. Otherwise, reduce arguments from left to right.
5. Stop when neither the head nor any argument can be reduced.

The current beta-reduction code is:

```python
head_substituted = (
    self.head.t
        .subst(0, self.args[0].shift(1, 0))
        .shift(-1, 0)
)
```

This rewrites the function body before continuing evaluation.

## 3. Important evaluation-order issue

The current evaluator applies an `Abs` before evaluating its argument.

For example:

```text
(λx. 1) argument
```

The evaluator can return `1` without first fully evaluating `argument`, because `x` is not used in the function body.

A standard CEK machine is normally call-by-value. It evaluates the argument before applying the function.

Therefore, directly implementing a standard call-by-value CEK machine may change PGSN behavior.

To preserve the current behavior, the first prototype will test storing an unevaluated argument together with its environment, similar to a thunk or delayed closure.

For this reason, the implementation may be described initially as a:

> CEK-style environment-based evaluator

The exact machine design will be decided after testing the basic lambda subset.

Note: the current PGSN evaluator can also reduce expressions inside an `Abs` body. Preserving this behavior is a known compatibility issue, but it is outside the first internship prototype.

## 4. First prototype scope

| PGSN term or feature     | First prototype | Reason                                                       |
| ------------------------ | --------------- | ------------------------------------------------------------ |
| `Variable`               | Required        | Must retrieve a binding from the environment                 |
| `Abs`                    | Required        | Must produce a closure                                       |
| `App`                    | Required        | Must evaluate function application                           |
| `String`                 | Required        | Basic constant value                                         |
| `Integer`                | Required        | Basic constant value                                         |
| `Boolean`                | Required        | Basic constant value                                         |
| Environment              | Required        | Stores variable bindings                                     |
| Closure                  | Required        | Stores an abstraction together with its environment          |
| Delayed argument binding | Required        | Preserves PGSN behavior without eagerly evaluating arguments |
| Continuation/frame       | Required        | Records what evaluation should do next                       |
| `Builtin`                | Later           | Requires PGSN-specific argument and application behavior     |
| `List`                   | Later           | Requires container traversal and evaluation-order handling   |
| `Record`                 | Later           | Requires attribute evaluation                                |
| `PGSNClass`              | Later           | Requires inheritance, defaults, attributes, and methods      |
| `PGSNObject`             | Later           | Requires object construction and attribute lookup            |

## 5. Proposed machine components

The first prototype should contain the following concepts.

### Control

The term currently being evaluated.

Examples:

```text
Variable
Abs
App
Integer
String
Boolean
```

### Environment

A mapping from variables to values or delayed computations.

Its purpose is to avoid immediately substituting an argument throughout the complete function body.

### Closure

A lambda abstraction stored together with the environment in which it was created.

Conceptually:

```text
Closure = function body + saved environment
```

The saved environment allows free variables in the function body to retain their original meanings.

### Delayed argument binding

The current PGSN evaluator does not always evaluate an argument before applying an abstraction.

The first prototype will therefore test storing an argument without evaluating it immediately.

Conceptually:

```text
Delayed argument = argument expression + saved environment
```

The saved environment is needed so that variables appearing inside the argument retain the meanings they had where the argument was created.

If the corresponding function parameter is never used, the delayed argument should not need to be evaluated.

### Continuation

A representation of the remaining work.

For an application, it may need to remember:

* That a function is being evaluated.
* Which argument belongs to the application.
* Which environment belongs to that argument.
* What computation should continue afterward.

## 6. Initial correctness examples

The first prototype should be compared with the current evaluator using small lambda terms.

### Identity

```text
(λx. x) 5
```

Expected result:

```text
5
```

### Constant function

```text
(λx. 1) 5
```

Expected result:

```text
1
```

### Captured variable

```text
((λx. λy. x) 5) 10
```

Expected result:

```text
5
```

This checks whether a closure preserves the environment containing `x`.

### Nested application

```text
(λf. f 5) (λx. x)
```

Expected result:

```text
5
```

### Evaluation-order test

Use a constant function with an argument that requires additional evaluation:

```text
(λx. 1) complicated_argument
```

The current evaluator may return `1` without evaluating the unused argument.

The environment-based prototype should reproduce this behavior for the lambda subset.

This test determines whether delayed argument handling can preserve the existing evaluator's application behavior.

## 7. First prototype stopping point

The first prototype is complete when:

* Variables are resolved through an environment.
* An abstraction produces a closure.
* Applications work without beta substitution.
* Arguments can be stored as delayed computations instead of always being evaluated before application.
* The identity example works.
* The constant-function example works.
* The captured-variable example works.
* The nested-application example works.
* The evaluation-order test confirms that an unused argument is not evaluated before function application.
* Results are compared with the current evaluator.
* The evaluation-order difference is documented.

The first prototype does not need to evaluate complete XML PGSN examples.

Preserving evaluation inside an unapplied `Abs` body is not required for this first prototype.

## 8. Later implementation stages

### Stage 2: Built-ins and multiple arguments

Add:

* `Builtin`
* Applicable-argument checks
* Multiple arguments
* Current built-in evaluation behavior

### Stage 3: Containers

Add:

* `List`
* `Record`
* Left-to-right traversal
* Conversion to Python values

### Stage 4: PGSN-specific objects

Add:

* `PGSNClass`
* `PGSNObject`
* Inheritance
* Defaults
* Attributes
* Methods

### Stage 5: CLI integration

Allow the evaluator to be selected, for example:

```bash
pgsn profile input.xml --engine substitution
pgsn profile input.xml --engine environment
```

Both evaluators must:

* Receive the same input.
* Produce the same output.
* Be measured under comparable conditions.

## 9. Final comparison requirements

The final comparison should measure:

* Correctness
* Evaluation time
* Evaluation steps
* Current evaluator beta reductions
* Current shift and substitution visits
* Environment lookups
* Closure creation
* Continuation transitions
* Memory usage, if practical

Detailed counters should be disabled when measuring clean execution time.

## 10. Current conclusion

The baseline results justify implementing an environment-based evaluator because repeated shifting is a major cost in the current evaluator.

However, the new evaluator must preserve PGSN semantics. In particular, the current evaluator applies lambda abstractions before fully evaluating their arguments, while a standard CEK machine is normally call-by-value.

Therefore, the first internship prototype will test a CEK-style environment-based evaluator with delayed argument handling on the basic PGSN lambda subset.

A complete replacement evaluator for all PGSN features is outside the scope of the first prototype.
