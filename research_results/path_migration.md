# Research evidence path migration

Prepared on `research/reorganize-experiment-results`, from consolidation commit
`8cdd09d9b47e17204dd74b5d8beaded08435e628`. Only locations and active navigation
change; all 54 files listed in [the SHA-256 ledger](evidence_hashes_sha256.csv)
retain their exact bytes. SHA-256 is a content fingerprint used to detect changes.
The ledger includes both moved datasets, historical archives, and current-PGSN
run evidence and READMEs. Editable indexes/reports are reviewed in the Git diff.

| Original path | Current path |
|---|---|
| `experiments/cek_machine/results/basic_benchmark_validation/` | `research_results/cek/basic_validation/2026-10-14/` |
| `docs/data/cbv_cek_milestone3_validation.csv` | `research_results/cek/recursion_validation/2026-10-11/cbv_cek_milestone3_validation.csv` |

The moved basic README and metadata are immutable records: their old output
command describes the original run. Use the commands below today. The recursion
report likewise labels its original commands as historical. Historical archives
and the current-PGSN run were not moved or edited. Source code remains under
`experiments/cek_machine/`; milestone reports/plans remain under `docs/`.

## Saved-data checks (no benchmark evaluation)

Run from the repository root in the existing Python environment:

```sh
.venv/bin/python -B experiments/cek_machine/benchmark_basic_validation.py --verify-only --runs 500 --sizes 10 100 200
.venv/bin/python -B experiments/cek_machine/analyze_recursion_validation.py research_results/cek/recursion_validation/2026-10-11/cbv_cek_milestone3_validation.csv
.venv/bin/python -B experiments/performance/current_pgsn_benchmark.py --verify-only --output research_results/current_pgsn/runs/2026-10-19_current_pgsn_examples
```

The basic verifier defaults to the moved 2026-10-14 dataset. The recursion
analysis accepts an explicit CSV path; it uses saved summary columns for its
regressions, rather than independently verifying every raw statistic. The
current-PGSN verifier also checks source/dependency hashes against this checkout.

## Future reproduction (not executed for this reorganization)

Use a fresh directory, replacing `<unique-run-id>` with an unused run name.
The basic and current-PGSN harnesses refuse existing output directories.
Recursion writes CSV to stdout; create a new run directory first and use shell
`noclobber` so redirection cannot overwrite an existing file:

```sh
.venv/bin/python experiments/cek_machine/benchmark_basic_validation.py --warmups 20 --runs 500 --sizes 10 100 200 --output research_results/cek/basic_validation/<unique-run-id>
mkdir research_results/cek/recursion_validation/<unique-run-id>
(set -C; .venv/bin/python experiments/cek_machine/benchmark_recursion.py --warmups 20 --runs 500 --sizes 0 10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 > research_results/cek/recursion_validation/<unique-run-id>/cbv_cek_milestone3_validation.csv)
.venv/bin/python experiments/performance/current_pgsn_benchmark.py --output research_results/current_pgsn/runs/<unique-run-id>
```

Record the source commit and environment before any future run. Consult the
original reports for timing scope and limitations; changed hardware or software
will not reproduce identical durations. No new measurements are part of this migration.
