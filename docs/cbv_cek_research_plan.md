# CBV CEK research plan

## Motivation and research boundary

Investigate an explicit environment machine as an alternative to repeated
substitution and shifting. Correctness and reproducible semantic evidence come
before performance. This experiment does not claim equivalence to all PGSN.

Experiment A remains on `research/env-evaluator-py-support` at
`dea6441a505b14c17adba0ba5abccd3c17494ab6`. It uses delayed arguments and Python
calls (plus a bounded structured path) to preserve production behavior. This
experiment starts independently from upstream/main
`65e90567031f8843d785778b42aad5a9084bd57d`, without merging or copying A's evaluator.
The requested strict CBV semantics deliberately evaluate unused arguments.

## Machine and invariants

State is `<Control, Environment, Continuation>`, represented by frozen data
classes. Control is nameless syntax or a runtime value. Environments are tuples
of evaluated runtime values, indexed by the existing de Bruijn number. Closures
capture a body and lexical environment; application prepends the argument value.
Runtime values are primitive Integer/String/Boolean/Constant Terms, Closure,
or PartialBuiltin. PartialBuiltin retains only evaluated arguments.

Halt completes evaluation. AppFunction saves the argument syntax, its lexical
environment and remaining continuation. AppArgument saves the function value
and remaining continuation. Function then argument are evaluated left to right.
The evaluator uses an iterative single-transition loop, never recursive subterm
evaluation. Name removal is permitted once at entry; it remains recursive.
No fully_eval, eval, eval_or_none, shift, shift_or_none, subst or subst_or_none
may be called during evaluation. There is no production fallback.
Public low-level State/step construction assumes nameless syntax and value-only
environments; the evaluate entry point establishes these invariants itself.

## Milestone 1 scope and verification

Support Variable, Abs, App, Integer, String, Boolean, Constant and curried
Plus/Minus/Times/Div/Mod only. Reuse arithmetic applicability/computation only
after evaluating arguments. Keep all evaluator changes outside production.
Test each continuation transition, primitive and arithmetic family, lexical
capture/shadowing, functions as arguments, nested applications, partial values
and their later application, strict unused arguments and left-to-right order.
Compare terminating shared cases with production. Guard all seven forbidden
Term methods while running a lambda/arithmetic case. Check explicit errors and
iterative evaluation of deep nameless input. Run focused and complete suites,
compile new Python files, inspect the diff and run git diff --check.

## Explicit non-scope

No List, Record, IfThenElse, Guard, Map, Fold, DefineClass, PGSNClass,
PGSNObject, fix integration, XML, examples/cli.py or other real GSN examples.
No benchmarks, production replacement, general runtime-to-Term conversion,
or Milestone 2 implementation. Existing upstream suite coverage does not imply
that this machine supports those features.

## Milestone 1 status (historical)

Milestone 1 implementation and verification complete: 31 focused tests and
376 full-suite tests pass; baseline was 345. Compilation and diff whitespace
checks pass. One final checkpoint commit and push are the delivery actions.
No later-milestone features are complete or authorized here.

## Deferred questions for user review

- Is strict CBV the intended language contract, given unused-argument differences?
- Should primitive runtime values remain Terms or become distinct runtime data?
- How should escaping closures and partial builtins be presented to callers?
- Should invalid applications remain explicit errors or represent stuck Terms?
- Should free variables, step budgets and divergence have dedicated APIs/errors?
- How should entry-boundary recursion and environment allocation be measured?

Review these questions before defining any future milestone. No performance
conclusion or broad semantic equivalence follows from this milestone.

## Milestone 2 update (2026-09-22)

The measurement branch starts from current upstream `1afc1909cee32dfc6c686e5e665b07fdd355b639` and restores these four files from Milestone 1 commit `57b288cd78ec552cf1e1fee638ed6b3136824338`. Current builtins use `apply_args_or_none`; free-bound pruning substantially changed the evaluator cost. This milestone measures only successful shared scalar lambda/arithmetic cases. See [Milestone 2 results](cbv_cek_milestone2_results.md) for methodology, counter definitions, results, and limits. No production integration or later feature work is included.

## Basic record support (2026-10-28)

On `research/cek-record-support`, based on `d964044`, the experimental machine
supports finite records whose fields evaluate to Integer, String, Boolean or
Constant. This extends the historical Milestone 1 scope above; it does not
claim full production compatibility. See [implementation](../experiments/cek_machine/cbv_cek.py)
and [focused tests](../experiments/cek_machine/test_cbv_cek.py).

Every field is evaluated strictly, once in insertion order, before lookup.
`RecordField` continuations preserve the record's lexical environment between
fields and restore the enclosing continuation when construction finishes.
`RecordValue` holds evaluated labelled fields and can pass through lambdas and
closures. Applying it to a String selects the corresponding primitive value.
Missing keys raise KeyError; non-String keys raise TypeError. Unsupported field
values and operations fail explicitly, with no production-evaluator fallback.

Current can select a valid field without evaluating an invalid unselected field;
strict CEK deliberately evaluates both. Current may retain an unresolved lookup
where CEK raises an error. Successful shared cases are compared in the tests.

Closure-valued fields, partial-builtin fields, nested record values, lists,
merging/overwriting, keyword arguments/defaults, classes/objects, XML and GSN
rendering remain unsupported. RecordValue is not a production Record Term;
no automatic runtime-to-Term readback was added. No performance claims or new
measurements accompany this extension; earlier results identify their own source
checkpoints and are unchanged.
