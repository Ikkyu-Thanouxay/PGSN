# Milestone 2: controlled CEK measurements

Starting point: upstream/main `1afc1909cee32dfc6c686e5e665b07fdd355b639`. The four Milestone 1 files came from `57b288cd78ec552cf1e1fee638ed6b3136824338`; the old branch and commit are preserved. This branch starts at current upstream so it measures the evaluator after PR #68 changed builtins to `apply_args_or_none` and after the cached `free_bound()` pruning of shifts and substitutions. The question is how much rewriting remains on shared successful programs and how the value-environment CEK scales.

## Method

Run `python experiments/cek_machine/benchmark.py` from the repository root. The runner builds a **nameless** term outside timing, checks the expected result and agreement, makes one counter pass, then runs 3 warm-ups and 11 recorded runs per evaluator. Values below are medians of `perf_counter()` durations in milliseconds. CEK total, entry `remove_name()`, and machine loop are timed separately; medians of components need not sum exactly to the total median. Detailed counters are absent from timing runs. The production timing uses `fully_eval` and the CEK timing uses its uninstrumented `initial_state`/`step` loop. These nameless inputs make name removal nearly free; this experiment does not quantify named-source conversion cost. The counters are event counts, not comparable units of work.

Identity nests `I = λx.x` around 7. Captured nests `(λx.(λy.x)) value 0`, returning 7 while exercising capture and lookup. Arithmetic nests curried `plus` applications, returning the depth. All are supported by both evaluators. A recursion error in either verification path excludes a size; no recursion limit was changed. The metrics pass mirrors `fully_eval`'s outer loop with a 10,000-step budget.

Python 3.14.7, pytest 8.4.2, local macOS workspace, 2026-09-22. Clean upstream baseline: `python -m pytest -q`: **534 passed, 4 deselected in 6.89s** (wall time 7.10s).

## Counter definitions

- **root**: successful outer `eval_or_none` progressions; the final unsuccessful check is excluded.
- **beta**: `Context.reduce_or_none` entries with an `Abs` head and at least one argument, the actual lambda reduction branch.
- **shift/subst visits**: entries to public `Term.shift_or_none` / `Term.subst_or_none`, including recursively reached terms. A visit is one operation entry, not one distinct object or a CEK transition.
- **pruned**: those entries where `free_bound() <= cutoff` (shift) or `free_bound() <= variable` (subst), so the public method immediately returns without traversing children.
- **transitions**: successful CEK `step()` calls before Halt; **lookups**: transitions whose control is a Variable.
- **closures/builtins**: transitions applying a Closure or completing an arithmetic builtin with its final evaluated argument. **environment extensions**: Closure applications that prepend one value.
- **AppFunction/AppArgument frames**: transitions creating each frame type. **maximum continuation depth**: largest number of linked frames observed before a transition or at Halt. Depth traversal adds overhead only to the counter pass.

Research wrappers on `Term` and `Context` are restored in `finally`, including exceptions. They do not edit production source.

## Controlled results

Times in ms. `R/B/S/U` means root, beta, shift visits, subst visits. `SP/UP` are shift and subst pruned calls. `T/L/C/A/E/D` means CEK transitions, lookups, Closure applications, builtin applications, Environment extensions, and maximum continuation depth. The runner also prints both frame creation counts.

| Family | n | Current | CEK total | remove | loop | R/B/S/U | SP/UP | T/L/C/A/E/D |
|---|---:|---:|---:|---:|---:|---|---|---|
| identity | 10 | 0.059 | 0.030 | 0.000 | 0.030 | 10/10/20/10 | 20/0 | 50/10/10/0/10/10 |
| identity | 100 | 2.267 | 0.292 | 0.000 | 0.292 | 100/100/200/100 | 200/0 | 500/100/100/0/100/100 |
| identity | 200 | 8.275 | 0.573 | 0.001 | 0.572 | 200/200/400/200 | 400/0 | 1000/200/200/0/200/200 |
| captured | 10 | 0.152 | 0.056 | 0.000 | 0.055 | 20/20/50/30 | 50/10 | 90/10/20/0/20/20 |
| captured | 100 | 1.518 | 0.536 | 0.000 | 0.536 | 200/200/500/300 | 500/100 | 900/100/200/0/200/200 |
| captured | 200 | 3.051 | 1.076 | 0.000 | 1.075 | 400/400/1000/600 | 1000/200 | 1800/200/400/0/400/400 |
| arithmetic | 10 | 0.417 | 0.063 | 0.000 | 0.063 | 10/0/0/0 | 0/0 | 70/0/0/10/0/20 |
| arithmetic | 100 | 75.515 | 0.632 | 0.002 | 0.630 | 100/0/0/0 | 0/0 | 700/0/0/100/0/200 |
| arithmetic | 200 | 475.562 | 1.273 | 0.003 | 1.271 | 200/0/0/0 | 0/0 | 1400/0/0/200/0/400 |

Sizes 500, 1000, and 2000 each raised `RecursionError: maximum recursion depth exceeded` for all three families during the shared benchmark path. This is a real boundary of these nested terms with the current Python evaluator; there are no timing comparisons at those sizes.

The optimized evaluator pruned every shift call in these lambda cases, yet still paid for root progression, context rebuilding, substitution calls, and Python object work. Arithmetic has zero shift and substitution visits; its steep timing growth here therefore cannot be attributed to rewriting counters alone. CEK event counts grow linearly in all successful ranges, while these local timings differ by family. Captured terms are particularly useful because their environment lookups and extensions are visible. This bounded result supports further environment-machine research; it does not establish a complete PGSN speedup.

## SolarWinds context

`PGSN-implementation.md` reports an upstream author's historical change from about **396 s** before free-bound pruning to about **0.9 s** after it, for `examples/SolarWinds.xml`. On this machine, compiling that XML outside the timed region and timing the current compiled term's `fully_eval()` gave **0.616 s median**, with 3 warm-ups and 11 recorded runs. This is a **current evaluator context measurement — NOT a CEK comparison**. No SolarWinds CEK run was made.

## Semantic boundary

Current PGSN and strict CBV are not completely semantically equivalent. Current PGSN leaves an unreducible builtin application as a stuck term, rather than an evaluator exception. The minimal CEK's `ExperimentalStuckError` is only an experiment signal; final stuck-term/readback behavior is absent. Strict CBV evaluates an unused argument that PGSN may skip. Current `fix` is not integrated with CBV. List, Record, classes, objects, conditionals, XML, real GSN, and SolarWinds are unsupported by this CEK. Name removal, closure readback, recursion, and builtin forcing need later design. Milestone 2 neither establishes production readiness nor proves a complete PGSN performance improvement.
