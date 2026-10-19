# Fresh current-PGSN real-example measurements

Source/harness commit: `607b369274276d40283597b6e0bea1a6a9ffeb76` on `research/performance-data-consolidation`.
Source tree was clean at launch; generated results were committed separately.
Run UTC: 2026-10-18T18:02:49.300394+00:00 to 2026-10-18T20:33:53.601655+00:00.

This dataset measures optimized production PGSN only. It is not a CEK comparison.
No production evaluator semantics were changed. Every evaluation has an isolated
fresh Python process; tests and other benchmark processes did not overlap the run.

## Files and boundaries

- `sources.csv`: all 53 sources, content hashes, sizes, XML dependency hashes/bytes and eligibility.
- `pilot.csv` and `pilot.json`: one clean pilot per eligible input and repetition choices.
- `raw_samples.csv` and `raw_samples.json`: every warmup and measured clean sample; JSON also retains per-worker environment.
- `summary.csv`: per-source statuses and statistics derived from measured raw samples only.
- `counters.csv` and `counters.json`: separate operation-count passes, with explicitly diagnostic elapsed fields.
- `profiles/*.json` and `profiles/*.txt`: evaluation-only cProfile diagnostics, no counters.
- `metadata.json`: source, environment, command, timing clock, GC, budget, timeouts and order.
- `validation.json`: saved-data verification result.

All timing fields are seconds. `load_seconds` includes initial PGSN imports and
XML compilation or allowlisted Python import/construction. `eval_seconds` uses
`fully_eval(steps=1000000)` including API name removal when needed.
`gsn_seconds` converts the already evaluated value with `gsn_tree`; it does not
evaluate again. `output_seconds` generates textual Tree.show output with
`stdout=False, sorting=False, idhidden=True, line_type=ascii-ex`.
SHA-256 hashes UTF-8 text outside evaluation timing. Hidden random UUIDs do not
enter textual output. Repeatability is evidence, not an independent proof of semantics.

`worker_total_seconds` independently measures loading through hashing, excluding
interpreter startup, worker standard-library imports, environment extraction and
JSON transport. `process_wall_seconds` includes all subprocess startup/completion.
Total medians are computed from total samples, never added phase medians.

Pilot worker-total policy (warmups/measured): <0.1s 5/50; <1s 3/20;
<10s 2/10; <60s 1/5; otherwise 0/3. All choices were saved before main runs.
Warmups are separate fresh processes and warm only system/OS state, not shared
evaluator caches. No outliers removed. Quartiles use inclusive interpolation;
SD is sample SD. Clean timeout 1800s; diagnostic timeout 3600s.

Counters use the CEK-research definitions: root successful outer progressions,
lambda-headed Context reductions, public shift/subst entries, and free_bound
pruned entries. Initial name removal is outside counter wrappers. Counter-loop
elapsed time is diagnostic, never clean timing. cProfile includes only fully_eval
after loading, including API name removal; recursive cumulative times are not
independently additive costs. See [harness documentation](../../../../experiments/performance/README.md).

## Clean medians for key inputs

| Input | n | Load | fully_eval | GSN conversion | Output | Worker total | Process wall |
|---|---:|---:|---:|---:|---:|---:|---:|
| examples/SolarWinds.xml | 20 | 0.051207 | 0.617027 | 0.002151 | 0.000619 | 0.671179 | 0.728592 |
| examples/EU_AI_ACT/case_proctoring.xml | 3 | 0.056580 | 335.957296 | 0.001404 | 0.000414 | 336.016038 | 336.075229 |
| examples/EU_AI_ACT/case_medical_ai.xml | 3 | 0.056138 | 139.182364 | 0.000795 | 0.000188 | 139.256843 | 139.328856 |
| examples/EU_AI_ACT/case_gpai_system.xml | 3 | 0.056254 | 152.544969 | 0.000742 | 0.000176 | 152.602178 | 152.665903 |
| examples/EU_AI_ACT/case_recruitment_ai.xml | 3 | 0.056380 | 139.195157 | 0.000822 | 0.000195 | 139.265202 | 139.334736 |

## Every runnable source and selected policy

| Input | Status | Warmups / runs | Eval median s | Worker total median s |
|---|---|---:|---:|---:|
| examples/Componentwise_Hazard_Analysis/System.xml | ok | 5 / 50 | 0.034295 | 0.085314 |
| examples/EU_AI_ACT/case_gpai_system.xml | ok | 0 / 3 | 152.544969 | 152.602178 |
| examples/EU_AI_ACT/case_medical_ai.xml | ok | 0 / 3 | 139.182364 | 139.256843 |
| examples/EU_AI_ACT/case_proctoring.xml | ok | 0 / 3 | 335.957296 | 336.016038 |
| examples/EU_AI_ACT/case_proctoring_simplified.xml | ok | 2 / 10 | 4.814716 | 4.868532 |
| examples/EU_AI_ACT/case_recruitment_ai.xml | ok | 0 / 3 | 139.195157 | 139.265202 |
| examples/Figure6/figure6_plain.xml | ok | 5 / 50 | 0.016479 | 0.066351 |
| examples/Figure6/figure6_programmatic.xml | ok | 5 / 50 | 0.018464 | 0.068659 |
| examples/SolarWinds.xml | ok | 3 / 20 | 0.617027 | 0.671179 |
| examples/Tracability/trace.xml | ok | 5 / 50 | 0.011879 | 0.061928 |
| examples/cap-a.xml | ok | 5 / 50 | 0.031066 | 0.080634 |
| examples/custom_goal.xml | ok | 5 / 50 | 0.001249 | 0.050268 |
| examples/defeaters.xml | ok | 5 / 50 | 0.012816 | 0.062606 |
| examples/gsn-ja.xml | ok | 5 / 50 | 0.006284 | 0.055861 |
| examples/gsn.xml | ok | 5 / 50 | 0.004752 | 0.054398 |
| examples/map_term.xml | ok | 5 / 50 | 0.005684 | 0.055416 |
| examples/robot.xml | ok | 5 / 50 | 0.015951 | 0.065836 |
| examples/secure.xml | ok | 5 / 50 | 0.004747 | 0.054282 |
| examples/secure_with_template.xml | ok | 5 / 50 | 0.006413 | 0.056065 |
| examples/ssl_lib/factory_hmi.xml | ok | 5 / 50 | 0.010995 | 0.061369 |
| examples/ssl_lib/medical_app.xml | ok | 5 / 50 | 0.018967 | 0.069873 |
| examples/syntax-ja.xml | ok | 5 / 50 | 0.007130 | 0.057360 |
| examples/syntax.xml | ok | 5 / 50 | 0.007106 | 0.057164 |
| examples/undeveloped.xml | ok | 5 / 50 | 0.004579 | 0.054098 |
| examples/SolarWinds.py | error |  /  |  |  |
| examples/cap-a.py | ok | 5 / 50 | 0.029958 | 0.079551 |
| examples/cli.py | ok | 5 / 50 | 0.004768 | 0.053824 |
| examples/gsn.py | ok | 5 / 50 | 0.004718 | 0.054120 |
| examples/map_term.py | ok | 5 / 50 | 0.005246 | 0.054579 |

## Metadata-only inputs

All 17 PGSNModule XML files are metadata-only. `eu_ai_act_full.xml` is a
module/generator, with no standalone runtime. The four full wrappers above
import it; each wrapper’s source metadata lists all five transitive local XML
dependencies and their SHA-256 hashes and bytes. Aggregate dependency bytes
exclude the entry source itself; source-plus-dependency bytes are also recorded.

- `examples/build_gsn.py`: JSON-building helper; no module-level Term main.
- `examples/custom_goal.py`: import executes evaluation/show/render.
- `examples/robot.py`: import executes evaluation/printing and installs typeguard import hooks.
- `examples/secure.py`: import executes evaluation/show/render.
- `examples/secure_with_template.py`: import executes evaluation/show/render.
- `examples/tree.py`: Term constructed only under __main__.
- `examples/undeveloped.py`: import executes evaluation/show/render.

## Key operation counts

| Input | Status | Root | Beta | Shift visits | Subst visits | Shift pruned | Subst pruned |
|---|---|---:|---:|---:|---:|---:|---:|
| examples/SolarWinds.xml | ok | 517 | 1769 | 5562 | 18349 | 5562 | 8097 |
| examples/EU_AI_ACT/case_proctoring.xml | ok | 237620 | 395683 | 2273157 | 7137585 | 2273157 | 2783677 |
| examples/EU_AI_ACT/case_medical_ai.xml | ok | 124940 | 204856 | 1176877 | 3694918 | 1176877 | 1440731 |
| examples/EU_AI_ACT/case_gpai_system.xml | ok | 137920 | 225464 | 1294003 | 4060971 | 1294003 | 1582836 |
| examples/EU_AI_ACT/case_recruitment_ai.xml | ok | 124804 | 206540 | 1185272 | 3720711 | 1185272 | 1450632 |

## cProfile diagnostics

These are instrumented profiles; their elapsed times are not benchmark results.

### examples/EU_AI_ACT/case_gpai_system.xml

Status: ok.

Cumulative leaders: `fully_eval` (`pgsn_term.py:142`), 568.051 s, 1 calls; `eval_or_none` (`pgsn_term.py:125`), 563.167 s, 170189850 calls; `_eval_or_none` (`pgsn_term.py:893`), 558.391 s, 15873869 calls; `_traverse` (`pgsn_term.py:880`), 558.330 s, 15873869 calls; `<lambda>` (`pgsn_term.py:894`), 555.771 s, 57197481 calls.
Self-time leaders: `_traverse` (`pgsn_term.py:701`), 92.642 s, 57833021 calls; `eval_or_none` (`pgsn_term.py:125`), 39.318 s, 170189850 calls; `__eq__` (`<attrs generated methods pgsn.pgsn_term.App>:16`), 36.193 s, 128633665 calls; `_traverse` (`pgsn_term.py:880`), 33.587 s, 15873869 calls; `__eq__` (`<attrs generated methods pgsn.pgsn_term.PGSNClass>:16`), 20.887 s, 93238220 calls.

### examples/EU_AI_ACT/case_medical_ai.xml

Status: ok.

Cumulative leaders: `fully_eval` (`pgsn_term.py:142`), 523.831 s, 1 calls; `eval_or_none` (`pgsn_term.py:125`), 519.617 s, 164546286 calls; `_eval_or_none` (`pgsn_term.py:893`), 515.486 s, 15292327 calls; `_traverse` (`pgsn_term.py:880`), 515.433 s, 15292327 calls; `<lambda>` (`pgsn_term.py:894`), 513.111 s, 55709275 calls.
Self-time leaders: `_traverse` (`pgsn_term.py:701`), 89.762 s, 55820739 calls; `eval_or_none` (`pgsn_term.py:125`), 37.485 s, 164546286 calls; `_traverse` (`pgsn_term.py:880`), 32.413 s, 15292327 calls; `__eq__` (`<attrs generated methods pgsn.pgsn_term.App>:16`), 30.059 s, 106819556 calls; `_eval_or_none` (`pgsn_term.py:530`), 19.035 s, 65130630 calls.

### examples/EU_AI_ACT/case_proctoring.xml

Status: ok.

Cumulative leaders: `fully_eval` (`pgsn_term.py:142`), 1329.321 s, 1 calls; `eval_or_none` (`pgsn_term.py:125`), 1321.250 s, 477251674 calls; `_eval_or_none` (`pgsn_term.py:893`), 1313.367 s, 45130769 calls; `_traverse` (`pgsn_term.py:880`), 1313.271 s, 45130769 calls; `<lambda>` (`pgsn_term.py:894`), 1308.723 s, 163281106 calls.
Self-time leaders: `_traverse` (`pgsn_term.py:701`), 272.671 s, 164858235 calls; `eval_or_none` (`pgsn_term.py:125`), 107.598 s, 477251674 calls; `_traverse` (`pgsn_term.py:880`), 96.125 s, 45130769 calls; `__eq__` (`<attrs generated methods pgsn.pgsn_term.App>:16`), 58.099 s, 203107869 calls; `_eval_or_none` (`pgsn_term.py:530`), 57.388 s, 190171491 calls.

### examples/EU_AI_ACT/case_recruitment_ai.xml

Status: ok.

Cumulative leaders: `fully_eval` (`pgsn_term.py:142`), 530.652 s, 1 calls; `eval_or_none` (`pgsn_term.py:125`), 526.375 s, 164692067 calls; `_eval_or_none` (`pgsn_term.py:893`), 522.194 s, 15297091 calls; `_traverse` (`pgsn_term.py:880`), 522.141 s, 15297091 calls; `<lambda>` (`pgsn_term.py:894`), 519.796 s, 55695503 calls.
Self-time leaders: `_traverse` (`pgsn_term.py:701`), 90.464 s, 55839450 calls; `eval_or_none` (`pgsn_term.py:125`), 37.849 s, 164692067 calls; `_traverse` (`pgsn_term.py:880`), 32.777 s, 15297091 calls; `__eq__` (`<attrs generated methods pgsn.pgsn_term.App>:16`), 30.745 s, 107409551 calls; `_eval_or_none` (`pgsn_term.py:530`), 19.200 s, 65090074 calls.

### examples/SolarWinds.xml

Status: ok.

Cumulative leaders: `fully_eval` (`pgsn_term.py:142`), 2.466 s, 1 calls; `eval_or_none` (`pgsn_term.py:125`), 2.420 s, 1030368 calls; `_eval_or_none` (`pgsn_term.py:893`), 2.398 s, 88596 calls; `_traverse` (`pgsn_term.py:880`), 2.398 s, 88596 calls; `<lambda>` (`pgsn_term.py:894`), 2.390 s, 382788 calls.
Self-time leaders: `_traverse` (`pgsn_term.py:701`), 0.515 s, 324287 calls; `eval_or_none` (`pgsn_term.py:125`), 0.227 s, 1030368 calls; `_traverse` (`pgsn_term.py:880`), 0.211 s, 88596 calls; `_eval_or_none` (`pgsn_term.py:530`), 0.141 s, 487595 calls; `<lambda>` (`pgsn_term.py:718`), 0.102 s, 609165 calls.

In this source, `pgsn_term.py:701` is `PGSNClass._traverse` and
`pgsn_term.py:880` is `PGSNObject._traverse`. The profiles show repeated
evaluation traversal and dispatch despite all counted shift calls being pruned
in these five key inputs. Counts and profiles describe this run; they do not
establish a universal cost model.

## XML/Python output evidence

Counterpart filenames do not establish equality. Comparing only successfully
measured counterpart candidates, using the same textual serialization:

- `examples/cap-a.py` / `examples/cap-a.xml`: hashes different.
- `examples/gsn.py` / `examples/gsn.xml`: hashes equal.
- `examples/map_term.py` / `examples/map_term.xml`: hashes equal.

## Historical SolarWinds context

Historical pre-free_bound reports describe several-minute execution. July’s
322.338548 s was measured with cProfile and counters together and is diagnostic.
Upstream documentation records about 396 s before pruning and about 0.9 s after.
M2 records a later optimized Current-only 0.616 s median (3 warmups, 11 runs),
with compilation excluded and no saved individual timing series. The fresh
fully_eval median above is a separate fresh-process measurement with retained
samples and explicit boundaries. Machine, source state, instrumentation and
cache conditions differ; no controlled historical speedup ratio is claimed.

## Validation and limitations

Before measurement, focused harness tests passed (14 tests); the normal project
suite passed with 591 passed and four slow examples deselected. No tests
overlapped measurements. The harness source was then committed and pushed.

Saved-data verification checks every summary statistic against raw samples,
pilot policy/counts, output hashes across pilot/warmup/measured/counter/profile,
source/dependency hashes, and diagnostic separation. The inventory contains
24 XML programs, 17 XML modules and 12 Python files. No current CEK or historical
archive data is duplicated or modified. Successful output hashes are stable;
this does not establish general semantic equivalence or full-program CEK support.

Errors/timeouts: examples/SolarWinds.py clean error

Environment: Python 3.14.7 (main, Aug  5 2026, 10:29:49) [Clang 21.0.0 (clang-2100.1.1.101)].
Platform: macOS-26.5.2-arm64-arm-64bit-Mach-O; machine arm64.
Installed distribution metadata version: 0.0.3.
Project pyproject.toml declares 0.0.4. Workers prepend repository src/ to
sys.path, so the source commit identifies evaluated code rather than the
installed distribution version label. No environment metadata was rewritten.

The Python SolarWinds pilot evaluated but failed GSN conversion at
`<root>.support.sub_goals` with an unexpected remaining App. Its error and
partial phase diagnostics are retained in pilot.json/pilot.csv; it has no
successful complete-pipeline aggregation or counterpart-equality claim.

UTC timestamps and perf_counter durations are separate clocks. An observed
counter-pass UTC span differs substantially from its perf_counter elapsed
duration; the cause is unknown. UTC subtraction is not used as a timing
sample. All reported durations use the recorded perf_counter clock.
This local run does not control system scheduling, frequency or thermal state.
