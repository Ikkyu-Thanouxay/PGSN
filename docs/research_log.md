# PGSN research log — strict CBV branch

## Prior research history

Upstream/main has no research log or experiments/cek_machine files. Preserve
Experiment A's complete history on `research/env-evaluator-py-support`, pinned
at `dea6441a505b14c17adba0ba5abccd3c17494ab6`. Its earlier log is available at
[the preserved checkpoint](https://github.com/Ikkyu-Thanouxay/PGSN/blob/dea6441a505b14c17adba0ba5abccd3c17494ab6/docs/research_log.md),
or with `git show dea6441a505b14c17adba0ba5abccd3c17494ab6:docs/research_log.md`.
Referencing that immutable history avoids merging A's implementation or making
its results appear to apply to this independent CBV experiment. No prior branch
or research result was overwritten.

## 2026-09-16 — Milestone 1: minimal strict CBV CEK

- Branch: `research/cbv-cek`.
- Initial checkout: `research/env-evaluator-py-support`, clean, at
  `dea6441a505b14c17adba0ba5abccd3c17494ab6`.
- Exact implementation starting commit: fetched upstream/main
  `65e90567031f8843d785778b42aad5a9084bd57d` (Weak normal form #54).
  Target branch was absent locally and in origin/upstream heads before creation.
- Origin: https://github.com/Ikkyu-Thanouxay/PGSN.git;
  upstream: https://github.com/yamagata-lab/PGSN.git (push disabled).
- Read the applicable root AGENTS.md and checked ancestor/nested instructions.
  No AGENTS.md exists on the fetched upstream base. Current user instructions
  supersede A's older delayed-evaluation, example-selection and multi-commit
  workflow. Inspected production Term and DSL definitions, arithmetic methods,
  A's evaluator, comparison tests, benchmark source (not executed), research
  log, experiment file inventory, and recent histories. No CBV plan existed.
- Existing environment: `.venv/bin/python`, Python 3.14.7, pytest 8.4.2.
  No dependency/configuration changes were needed.

### Commands and exact results

Before switching, Experiment A verification:

- `.venv/bin/python -m pytest -q experiments/cek_machine/test_pgsn_env_eval.py`
  — **30 passed in 0.14s**.
- `.venv/bin/python -m pytest -q` — **369 passed in 0.80s**.

Clean upstream baseline, before creating tracked files:

- `.venv/bin/python --version` — **Python 3.14.7**.
- `.venv/bin/python -m pytest --version` — **pytest 8.4.2**.
- `.venv/bin/python -m pytest -q` — **345 passed in 0.37s**.
- No pre-existing test failure. Counts differ because the upstream checkout
  has a different history and excludes A's experiment tests.

Milestone verification:

- `.venv/bin/python -m pytest -q experiments/cek_machine/test_cbv_cek.py`
  — **31 passed in 0.07s**.
- `.venv/bin/python -m pytest -q` — **376 passed in 0.36s**.
- `.venv/bin/python -m py_compile experiments/cek_machine/cbv_cek.py experiments/cek_machine/test_cbv_cek.py`
  — exit **0**, no output.
- `git diff --check` and `git diff --cached --check` — exit **0**, no output.
- Complete four-file diff reviewed; no production files, examples, existing
  tests, or unsupported-feature implementations changed.

### Implementation and observations

Added `cbv_cek.py`, direct focused tests, and the persistent research plan.
Frozen State explicitly holds control/environment/continuation. Halt,
AppFunction and AppArgument are explicit machine data. The loop performs one
transition at a time. Environments contain only evaluated runtime values;
closures contain their lexical environment and nameless body. PartialBuiltin
contains only evaluated arguments, not argument syntax or saved environments.
Primitive values reuse the four existing scalar Term classes. Arithmetic uses
only the existing applicability/computation methods after integer values exist.

All five arithmetic families and successful scalar lambda comparisons agree
with the current evaluator. Division uses existing integer floor division.
Unused arguments are deliberately strict: `(lambda x. 1) (div 1 0)` raises
ZeroDivisionError here, while production returns Integer(1). This is a semantic
change from Experiment A, not an equivalence claim. Function evaluation precedes
argument evaluation, including arithmetic effects/errors. Invalid application
and arithmetic type mismatches raise TypeError, unbound variables LookupError,
and unselected syntax UnsupportedTermError; no silent fallback or success.

The guard patches Term.fully_eval, eval, eval_or_none, shift, shift_or_none,
subst and subst_or_none to fail immediately; lambda plus arithmetic succeeds.
Source review confirms none are called by this evaluator. A 2,000-deep nameless
application test passes using explicit frames. Entry name removal still uses
production's recursive traversal, once, and is outside that stack-depth claim.

### Problems, limits and future questions

No failed implementation/test attempt. Initial fetch was blocked by sandbox
write access to .git/FETCH_HEAD; remote-head queries hit sandbox DNS restrictions.
Approved escalated Git commands resolved both. No credential workaround used.

Deliberately unsupported: List, Record, IfThenElse, Guard, Map/Fold, classes and
objects, fix integration, XML and real GSN examples. No benchmarks, production
replacement, or general reification to Terms. Existing full-suite XML/GSN tests
exercise upstream code only. No Milestone 2 work performed.

Runtime questions remain: separate scalar runtime types versus reused Terms,
rendering escaping closures/partials, and validating manually constructed
low-level states. evaluate establishes value-only environments; step assumes
callers maintain its documented nameless/value-only preconditions. Error/stuck
questions remain: whether to preserve production stuck applications, support
open terms, standardize error types, or impose transition budgets. Divergent
lambda input currently has no step limit. No fix combinator integration tested.

This proves the bounded strict CBV machine and its tested invariants, not full
PGSN equivalence, performance gains, constant memory use, or stack safety of
name removal. Next research step: review the strictness and error contract and
runtime representation before authorizing another milestone. Stop after the
single final checkpoint is pushed and branch/remote/clean-tree checks pass.

Checkpoint title: `Add minimal CBV CEK machine`. Its exact SHA is reported in
the handoff and obtainable with `git log -1 --format=%H research/cbv-cek`;
embedding its own hash would require another commit. The checkpoint consists
only of this log, the research plan, cbv_cek.py and test_cbv_cek.py.

## 2026-09-22 — Milestone 2: optimized evaluator measurements

Fetched upstream/main at `1afc1909cee32dfc6c686e5e665b07fdd355b639`. Preserved Milestone 1 source commit `57b288cd78ec552cf1e1fee638ed6b3136824338` on its old branch. Clean upstream baseline: Python 3.14.7, pytest 8.4.2, `python -m pytest -q`: 534 passed, 4 deselected in 6.89s. PR #68 changed the builtin API; current stuck terms and free-bound pruning informed this research-only update. The benchmark and full results are in [Milestone 2 results](cbv_cek_milestone2_results.md). All experiment code stays under `experiments/cek_machine`; no production evaluator source changed.

## 2026-09-29 — Milestone 3: Z-based pure-lambda recursion

Fetched both remotes and verified unchanged upstream/main
`1afc1909cee32dfc6c686e5e665b07fdd355b639`, Milestone 1
`57b288cd78ec552cf1e1fee638ed6b3136824338`, and Milestone 2
`9ad56c65d7ff6297bc01a6971db1d33246fabcd8`. Started from the latter on new branch
`research/cbv-cek-recursion`, with a clean working tree and no applicable
AGENTS.md files. Origin remains `Ikkyu-Thanouxay/PGSN`; upstream push is disabled.
No old research history or Milestone 2 numbers were rewritten.

Changed shared `dsl.fix` from Y to Z with reserved delayed binder `_fix_arg`.
Current remains the rewriting evaluator; the strict-CBV CEK needed no change.
The old Y-specific lazy-branch fixture now applies the fixed identity to force
actual divergence. The new Scott countdown uses the real DSL fix and only
Variable/Abs/App, returning identity after n predecessor traversals. Its tests
cover small inputs, bounded Y-versus-Z behavior, shared fix usage, and no fallback.

[Milestone 3 results](cbv_cek_milestone3_results.md) records commands, methodology,
timings, counters, and limits. Reused the existing timing helpers and metrics:
3 warm-ups and 11 recorded runs on the same nameless object, conversion outside
timing, separate instrumentation. Sizes 1, 2, 5, 10, 20, 50, 100, 150 succeeded;
200 hit RecursionError during construction/name removal, before either evaluator.
No larger probe or recursion-limit change followed. CEK was faster in this
controlled local run, with zero Builtin applications; this is no full-PGSN claim.

Python 3.14.7 / pytest 8.4.2: focused production tests 192 passed; new recursion
tests 7 passed; all research tests 40 passed; default suite 574 passed with
4 slow tests deselected. Full suite including slow tests:
`.venv/bin/python -m pytest -q -m ''` — **578 passed in 766.18s**, no deselections
or failures.
Compilation and whitespace checks passed. The checkpoint title is
`Add CBV-compatible recursion benchmark`; its exact SHA is resolved from the
branch and included in the handoff. Push only this new branch to origin.

Stopped before general Builtins, List/Record, XML/GSN CEK, recursive environments,
SolarWinds CEK, eu_ai_act_full CEK, or Milestone 4.
