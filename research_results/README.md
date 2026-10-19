# PGSN performance research evidence index

This index organizes retained evidence by evaluator provenance. Phase 1 archived
existing evidence without new measurements; Phase 2 adds fresh current-PGSN data.
[manifest.csv](manifest.csv) identifies datasets,
source/evaluator checkpoints, artifact commits, instrumentation, timing scope,
sample retention and limitations. Unknown values are explicitly unknown or
not-retained. Artifact commits identify retained versions, not necessarily the
commit or date when measurements were executed.

- [July historical archive](historical/pre_free_bound_2026-07-19/README.md):
  pre-free_bound rewriting evaluator; five raw cProfile text files, the
  baseline_metrics summary and eight before/after document outputs. Times used
  cProfile plus counters and are diagnostic, not clean timing samples. Operation
  counts are preserved. The June README references missing raw files, explicitly
  marked missing in the archive; they were not reconstructed.
- [September environment experiment](historical/environment_evaluator_2026-09-10/README.md):
  older delayed-argument evaluator versus historical pre-free_bound PGSN;
  two separate saved summary/report passes, without individual timing samples.
  No cProfile in timings; counters measured separately. This is not strict-CBV CEK.
- [CEK index](cek/README.md): current optimized PGSN with cached free_bound
  pruning versus experimental strict-CBV CEK on controlled synthetic programs.
  Links preserve canonical files in place. Basic validation has nine raw CSVs
  with 500 paired samples each, plus summary.csv and metadata.json. Recursion
  validation CSV has 500 samples per evaluator per size in JSON-array fields,
  alongside derived statistics/counters. Timing and counter passes are separate.
  M2/M3 original summaries retain medians/counters but not their 11-run raw samples.
- SolarWinds documentation figures remain in
  [PGSN-implementation.md](../PGSN-implementation.md); M2's optimized Current-only
  0.616 s context measurement remains in
  [the M2 report](../docs/cbv_cek_milestone2_results.md). These are distinct from
  July's instrumented 322.338548 s figure. No full SolarWinds or EU AI Act CEK
  comparison exists yet.
- [Fresh current PGSN dataset](current_pgsn/README.md): 24 XML programs and four
  Python inputs measured in isolated processes, with 29 pilots, 1,142 measured
  clean samples and 115 warmups. All 53 sources retain metadata and status.
  Clean timings, counters and cProfile diagnostics remain separate; see the run
  README for errors, policy, output hashes and limitations. No full-program CEK
  comparison is implied.

[Branch provenance](branch_provenance.md) records exact ancestry/checkpoints and
why historical evaluator code was not merged. Archive READMEs record original
paths and matching source/copy blob SHAs for every copied artifact. Historical
paths/commands inside immutable copied reports describe their original context;
missing June raw paths are explicitly missing, and historical implementation
references use exact-commit links rather than nonexistent current paths.

[examples.csv](examples.csv) is a static inventory of 24 PGSN XML programs,
17 PGSNModule XML modules and 12 Python files. XML modules are not eligible for
standalone evaluation. Python automatic eligibility means a statically observed
module-level Term candidate with no observed import evaluation/render call;
it does not assert import safety or benchmark completion. XML counterparts are
candidates only, not claims of output equality. Python files were AST-parsed,
never imported. Source hashes are Git blob hashes at the verified base.
