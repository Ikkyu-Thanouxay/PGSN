# Pre-free_bound historical evidence

Source branch: `research/cek-baseline-metrics`; exact source tip: `83e932ca0f1fd76ef2f9b85b1550fe783f72ff9c`.
Original directory structure is retained below this archive. Only reports/data were copied.
Static inspection of the source evaluator found no `free_bound` implementation.
“Current” in these historical reports means the evaluator at that historical checkpoint,
not current optimized PGSN.

July elapsed times were collected with both cProfile and explicit Python operation
counters active. They are diagnostic/instrumented elapsed times, not clean timing
samples. Raw profile text is diagnostic output, not a distribution of timing samples.
The baseline before/after outputs preserve document equivalence evidence for four
inputs; they are not benchmark timing samples. `baseline_metrics.md` is a summary.

SolarWinds 322.338548 s is the instrumented evaluation time reported for
`SolarWinds.xml`, with 448 evaluation steps, 1,426 beta reductions,
483,384,975 shift visits and 1,044,353 substitution visits. The operation counts
and ratios are important preserved evidence; visits count repeated operations,
not distinct nodes. Instrumentation overhead prevents comparison of this elapsed
time directly with clean optimized-PGSN or CEK timings. No timing repetitions or
individual clean samples are retained here.

The June README is preserved as a reference only. Its ten referenced raw June
files are **missing from the inspected repository history** (no reachable path
history found under `reports/profiler/2026-06-25/raw`). They have not been
reconstructed or invented. Links/paths inside copied reports retain their original
historical context; the missing June paths are explicitly missing.

Archived baseline output files are intentionally preserved byte-for-byte. Some
source files contain trailing whitespace and/or blank lines at EOF, so a full
`git diff --cached --check` reports warnings for these immutable archives.
These are historical-source properties, not newly introduced formatting.
The archive files must not be normalized because that would break blob identity.

Byte provenance was verified with `git rev-parse <source>:<original-path>` and
`git hash-object <copy>`; every pair matched. Copied contents are unchanged.

| Archived file | Original path at source tip | Source blob SHA | Copy blob SHA |
|---|---|---|---|
| [study/cek_machine/baseline_metrics.md](study/cek_machine/baseline_metrics.md) | study/cek_machine/baseline_metrics.md | f31c960a5f9f9efe264095442980b1f541ffb151 | f31c960a5f9f9efe264095442980b1f541ffb151 |
| [reports/profiler/2026-07-19/raw/profile_gsn.txt](reports/profiler/2026-07-19/raw/profile_gsn.txt) | reports/profiler/2026-07-19/raw/profile_gsn.txt | 267fbbd4cad09c453fd3391b1f5cf39c2e15844c | 267fbbd4cad09c453fd3391b1f5cf39c2e15844c |
| [reports/profiler/2026-07-19/raw/profile_map_term.txt](reports/profiler/2026-07-19/raw/profile_map_term.txt) | reports/profiler/2026-07-19/raw/profile_map_term.txt | 91ae6ef390e5c9ed6baae346b03743a6ebcb6a96 | 91ae6ef390e5c9ed6baae346b03743a6ebcb6a96 |
| [reports/profiler/2026-07-19/raw/profile_robot.txt](reports/profiler/2026-07-19/raw/profile_robot.txt) | reports/profiler/2026-07-19/raw/profile_robot.txt | 79616e27495f2fcf563507fc5bc739a6993e6ccd | 79616e27495f2fcf563507fc5bc739a6993e6ccd |
| [reports/profiler/2026-07-19/raw/profile_cap_a.txt](reports/profiler/2026-07-19/raw/profile_cap_a.txt) | reports/profiler/2026-07-19/raw/profile_cap_a.txt | a32de52dd23fae88f284c3799207a20fc718978e | a32de52dd23fae88f284c3799207a20fc718978e |
| [reports/profiler/2026-07-19/raw/profile_solarwinds.txt](reports/profiler/2026-07-19/raw/profile_solarwinds.txt) | reports/profiler/2026-07-19/raw/profile_solarwinds.txt | 636424b739226e5092555a5c2c2f625e4af204b1 | 636424b739226e5092555a5c2c2f625e4af204b1 |
| [reports/profiler/2026-07-19/baseline_outputs/gsn_before.txt](reports/profiler/2026-07-19/baseline_outputs/gsn_before.txt) | reports/profiler/2026-07-19/baseline_outputs/gsn_before.txt | 35591ba30b77a4b4ea58d7c24c95d7a4ec4627bc | 35591ba30b77a4b4ea58d7c24c95d7a4ec4627bc |
| [reports/profiler/2026-07-19/baseline_outputs/gsn_after.txt](reports/profiler/2026-07-19/baseline_outputs/gsn_after.txt) | reports/profiler/2026-07-19/baseline_outputs/gsn_after.txt | 35591ba30b77a4b4ea58d7c24c95d7a4ec4627bc | 35591ba30b77a4b4ea58d7c24c95d7a4ec4627bc |
| [reports/profiler/2026-07-19/baseline_outputs/map_term_before.txt](reports/profiler/2026-07-19/baseline_outputs/map_term_before.txt) | reports/profiler/2026-07-19/baseline_outputs/map_term_before.txt | 8435b69457942b5106d34e2f35ab125da85d2f62 | 8435b69457942b5106d34e2f35ab125da85d2f62 |
| [reports/profiler/2026-07-19/baseline_outputs/map_term_after.txt](reports/profiler/2026-07-19/baseline_outputs/map_term_after.txt) | reports/profiler/2026-07-19/baseline_outputs/map_term_after.txt | 8435b69457942b5106d34e2f35ab125da85d2f62 | 8435b69457942b5106d34e2f35ab125da85d2f62 |
| [reports/profiler/2026-07-19/baseline_outputs/robot_before.txt](reports/profiler/2026-07-19/baseline_outputs/robot_before.txt) | reports/profiler/2026-07-19/baseline_outputs/robot_before.txt | cffe9f67f4d64bd67fbff5b196752ed4d9fcea05 | cffe9f67f4d64bd67fbff5b196752ed4d9fcea05 |
| [reports/profiler/2026-07-19/baseline_outputs/robot_after.txt](reports/profiler/2026-07-19/baseline_outputs/robot_after.txt) | reports/profiler/2026-07-19/baseline_outputs/robot_after.txt | cffe9f67f4d64bd67fbff5b196752ed4d9fcea05 | cffe9f67f4d64bd67fbff5b196752ed4d9fcea05 |
| [reports/profiler/2026-07-19/baseline_outputs/cap_a_before.txt](reports/profiler/2026-07-19/baseline_outputs/cap_a_before.txt) | reports/profiler/2026-07-19/baseline_outputs/cap_a_before.txt | a91094190a778339b25506fecdcd0de26426cf27 | a91094190a778339b25506fecdcd0de26426cf27 |
| [reports/profiler/2026-07-19/baseline_outputs/cap_a_after.txt](reports/profiler/2026-07-19/baseline_outputs/cap_a_after.txt) | reports/profiler/2026-07-19/baseline_outputs/cap_a_after.txt | a91094190a778339b25506fecdcd0de26426cf27 | a91094190a778339b25506fecdcd0de26426cf27 |
| [reports/profiler/2026-06-25/README.md](reports/profiler/2026-06-25/README.md) | reports/profiler/2026-06-25/README.md | 15568e24900e75c45684f092600babe73b0d292d | 15568e24900e75c45684f092600babe73b0d292d |
