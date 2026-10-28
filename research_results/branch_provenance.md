# Branch provenance

Verified after fetching origin and upstream for inspection only on 2026-10-19.
Graph shows ancestry, not necessarily single parent edges (intermediate commits
are omitted). Historical branch and milestone branch tips were preserved.

```text
04d2bdedba3a90fe1a8d0187a6eae9c14344ff72
├── historical research path
│   └── research/cek-baseline-metrics 83e932ca0f1fd76ef2f9b85b1550fe783f72ff9c
└── later upstream development
    └── upstream/main 1afc1909cee32dfc6c686e5e665b07fdd355b639
        └── research/cbv-cek-metrics 9ad56c65d7ff6297bc01a6971db1d33246fabcd8
            └── research/cbv-cek-recursion d2c8be9e441b9edcb3beb23465d32b974df479dc
                └── research/cbv-cek-recursion-validation a5fccab2f2fe99677eae58fe86ee21a57ff71990
                    └── research/cbv-cek-basic-benchmark-validation 67e0579917eaeafe0acf7dc0e988e932d5e80799
                        └── research/performance-data-consolidation
```

`research/cbv-cek` at `57b288cd78ec552cf1e1fee638ed6b3136824338`
is the preserved Milestone 1 checkpoint. Its files were carried forward into
later work; it is not assumed to be a direct ancestor of the displayed M2 chain.

Local `main` and `origin/main` both resolve to `04d2bdedba3a90fe1a8d0187a6eae9c14344ff72`;
local main tracks upstream/main and is 46 commits behind. Origin's default HEAD
is origin/main. Upstream main is `1afc1909cee32dfc6c686e5e665b07fdd355b639`.
The old-versus-current symmetric difference is **20 historical-only / 50
current-only** commits (`git rev-list --left-right --count old...base`).

The old profiler branch is intentionally not merged: its evaluator implementation
and instrumentation belong to historical pre-free_bound research. Only selected
data/report blobs are archived, preserving evidence without importing historical
evaluator semantics.

Consolidation branch: `research/performance-data-consolidation`.
Branch base: `67e0579917eaeafe0acf7dc0e988e932d5e80799`.
The initial consolidation commit `4e107ec` added research evidence and indexes
under `research_results/`, without importing historical evaluator code.
Later commits on the same branch added the current-PGSN harness
(`607b369274276d40283597b6e0bea1a6a9ffeb76`), its measurements
(`0fba1d822860b3b3822b97c29814d753dd9a713a`), and midterm support
(`8cdd09d9b47e17204dd74b5d8beaded08435e628`).

The current run's artifact commit was verified with path history and the result
commit's tree: `0fba1d822860b3b3822b97c29814d753dd9a713a` first records
`research_results/current_pgsn/runs/2026-10-19_current_pgsn_examples/`.
This differs from the source/harness commit `607b369...` used for measurement.

The limited reorganization starts from `8cdd09d...` on the separate local branch
`research/reorganize-experiment-results`. The consolidation branch is preserved.
See [path migration](path_migration.md) and [evidence hashes](evidence_hashes_sha256.csv).
The branch graph and remote-state statements above describe the 2026-10-19
inspection, not a new fetch or new measurement.
