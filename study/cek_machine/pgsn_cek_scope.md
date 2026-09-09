# Scope of the PGSN Environment-Based Evaluator

Date: 2026-07-19
Updated: 2026-09-09 (Change Vision internship Day 3)

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

## 11. Change Vision internship Day 2 findings

Date: 2026-09-08

Day 2 began implementing the first environment-based evaluator using the real PGSN term classes in `src/pgsn/pgsn_term.py`.

The prototype is currently implemented in `experiments/cek_machine/pgsn_env_eval.py`.

### Environment representation

PGSN removes variable names before evaluation and uses de Bruijn indices.

The prototype uses an ordered environment where:

- `env[0]` is the nearest lambda binding.
- `env[1]` is the next outer binding.
- Higher indices refer to progressively outer bindings.

The initial prototype currently tests closed terms, so evaluation begins with an empty environment. Free-variable handling is deferred.

### Runtime representations

A `Closure` stores the function body together with the environment captured when the abstraction is encountered.

A `DelayedArgument` stores the unevaluated argument term together with the environment where that argument appeared.

Delayed arguments are not memoized in the current prototype.

### Basic application behavior

For a lambda application, the prototype:

1. Evaluates the function expression.
2. Produces a `Closure`.
3. Stores the argument as a `DelayedArgument` without evaluating it first.
4. Adds the delayed binding at environment index 0.
5. Evaluates the original function body under the extended environment.

The prototype lambda-application path does not perform beta substitution using `subst()` or beta-related `shift()` rewriting.

### Current successful tests

Using the real PGSN `Variable`, `Abs`, `App`, and `Integer` classes:

- `(lambda x. x) 5` -> environment evaluator: `5`; current evaluator: `5`
- `(lambda x. 1) 5` -> environment evaluator: `1`; current evaluator: `1`
- `((lambda x. lambda y. x) 5) 10` -> environment evaluator: `5`; current evaluator: `5`

The captured-variable test confirms that an inner closure can retain an outer binding through its captured environment.

These tests show matching observable results for the basic lambda subset tested so far. They do not establish full PGSN semantic compatibility.

### Current limitations and deferred issues

The prototype currently supports only:

- `Variable`
- `Abs`
- `App`
- Basic constants used by the prototype

The following remain unsupported:

- `Builtin`
- `List`
- `Record`
- `PGSNClass`
- `PGSNObject`
- Complete XML PGSN documents
- SolarWinds
- CLI evaluator selection

Known or deferred issues:

- Current PGSN can reduce expressions inside an unapplied `Abs` body, while the prototype currently turns an `Abs` directly into a closure.
- Free-variable environment handling has not yet been implemented.
- Delayed arguments currently do not use memoization.
- Only small closed lambda terms have been compared so far.
- A stronger unused-argument test with a reducible or unsupported argument would verify delayed evaluation more directly.

The next stage should extend the prototype carefully while continuing to compare its behavior with the current PGSN evaluator.

## 12. Change Vision internship Day 3 findings

Date: 2026-09-09

Day 3 focused on checking whether the current minimum environment-based prototype preserves important PGSN evaluation behavior.

### New comparison tests

Three new examples were compared using both the current PGSN evaluator and `eval_env()`.

    (lambda f. f 5) (lambda x. x) -> 5
    (lambda x. 1) (1 2) -> 1
    (lambda x. x) ((lambda z. z) 7) -> 7

All three produced the same result with both evaluators.

The unused-argument test is especially important:

    (lambda x. 1) (1 2) -> 1

The argument `(1 2)` would fail if evaluated because `1` is not a function.

Both evaluators returned `1`.

For `eval_env()`, this shows that an unused argument can remain delayed and does not need to be evaluated.

The used delayed-argument test:

    (lambda x. x) ((lambda z. z) 7) -> 7

shows the opposite behavior. The argument is delayed first, then evaluated later when `x` is actually needed.

Together:

    unused parameter -> delayed argument is not evaluated
    used parameter   -> delayed argument is evaluated when needed

### Remaining differences and open questions

#### Evaluation inside an unapplied `Abs`

Current PGSN can evaluate inside the body of an `Abs` before the abstraction is applied.

The prototype currently converts an `Abs` directly into a `Closure` without evaluating its body.

This is a real compatibility difference that must be considered later.

#### Free variables

The current prototype has only been tested with closed terms.

Free-variable behavior has not yet been implemented or verified.

#### Explicit Continuation / K

The prototype does not yet have an explicit Continuation state or continuation frames.

Python recursion currently controls what computation happens next.

Therefore, the current implementation is an:

> environment-based / CEK-style evaluator prototype

not a complete CEK machine.

#### Memoization

`DelayedArgument` does not cache its evaluated result.

This is not currently known to be a semantic difference from the existing PGSN evaluator.

Memoization is a possible future optimization and should be investigated separately.

### Day 3 conclusion

The minimum prototype preserved the tested PGSN application behavior for the supported lambda subset.

It showed that:

- functions can be passed through the environment;
- unused arguments can remain unevaluated;
- delayed arguments can be evaluated later when needed;
- the tested results match the current evaluator;
- the prototype application path avoids beta substitution and beta-related shift rewriting of the function body.

The next useful step is measurement and analysis rather than adding more PGSN features.
