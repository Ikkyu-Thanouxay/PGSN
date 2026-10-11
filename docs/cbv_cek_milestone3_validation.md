# Milestone 3 recursive benchmark validation

## Checkpoint and scope

Exact base: `d2c8be9e441b9edcb3beb23465d32b974df479dc`.
Branch: `research/cbv-cek-recursion-validation`.
The initial tree was clean on `research/cbv-cek-recursion`, at that exact commit.
Fetched origin and upstream; upstream/main remains
`1afc1909cee32dfc6c686e5e665b07fdd355b639`, identical to the upstream checkpoint
recorded in Milestone 3. No applicable AGENTS.md was found.
Upstream push is disabled; only the new branch is pushed to origin.

The shared Z combinator, countdown definition, evaluator semantics,
`cbv_cek.py`, production code, and historical Milestone 1/2/3 results are unchanged.
This is benchmark validation, not Milestone 4.

## Reproduction and method

Python 3.14.7; macOS-26.5.2-arm64-arm-64bit-Mach-O; 2026-10-11.
Python recursion limit remains 1000. From the repository root:

```sh
.venv/bin/python experiments/cek_machine/benchmark_recursion.py --warmups 20 --runs 500 --sizes 0 10 20 30 40 50 60 70 80 90 100 110 120 130 140 150 > docs/data/cbv_cek_milestone3_validation.csv
.venv/bin/python experiments/cek_machine/analyze_recursion_validation.py docs/data/cbv_cek_milestone3_validation.csv
```

Each size has 20 paired warm-ups and 500 paired measured runs. Current runs
first in each pair. Defaults remain 3 warm-ups and 11 runs. Raw individual
samples (JSON arrays inside CSV fields), summary statistics, and separate event
counters are preserved in [the data file](data/cbv_cek_milestone3_validation.csv).
SD is sample standard deviation; IQR uses inclusive interpolated quartiles.
All timing statistics are in milliseconds. No samples are trimmed.

The original Scott countdown uses only Variable, Abs, App and shared `dsl.fix`.
Both evaluators receive the same nameless term. Construction and `remove_name`
remain outside timing; neither is bypassed. CEK timing includes initialization
and its existing name-removal check. Results are checked on every run.
Metrics wrappers run separately before warm-up, never within measured timings.
The original perf_counter timing helpers and 10,000 Current step budget are
unchanged. Shared syntax retains cached free-variable bounds: these are warm
execution measurements, excluding front-end preparation cost.

An initial pass overlapped test execution and was discarded. The retained pass
ran after tests completed, with no concurrent test or benchmark process.
Every requested size prepared and evaluated successfully; no preparation
failure occurred in 0–150. No larger size was attempted.

## Timing and regression results

| n | Current median | mean | SD | IQR | CEK median | mean | SD | IQR |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.082021 | 0.082283 | 0.001816 | 0.001458 | 0.020499 | 0.020592 | 0.000658 | 0.000169 |
| 10 | 0.885333 | 0.886467 | 0.008314 | 0.008812 | 0.229125 | 0.229938 | 0.002937 | 0.002251 |
| 20 | 1.693813 | 1.696633 | 0.012676 | 0.013438 | 0.438209 | 0.439067 | 0.006102 | 0.004831 |
| 30 | 2.505688 | 2.508372 | 0.014621 | 0.020229 | 0.643875 | 0.644100 | 0.005851 | 0.006593 |
| 40 | 3.296750 | 3.299093 | 0.016738 | 0.019937 | 0.852937 | 0.854391 | 0.009750 | 0.013386 |
| 50 | 4.122063 | 4.131074 | 0.088448 | 0.024604 | 1.067834 | 1.069398 | 0.014620 | 0.023313 |
| 60 | 4.929479 | 4.934016 | 0.026495 | 0.030375 | 1.273812 | 1.274970 | 0.012606 | 0.017093 |
| 70 | 5.746083 | 5.747458 | 0.020098 | 0.028375 | 1.484416 | 1.485588 | 0.013812 | 0.016583 |
| 80 | 6.550021 | 6.578160 | 0.397573 | 0.039626 | 1.698312 | 1.703381 | 0.042204 | 0.023416 |
| 90 | 7.362812 | 7.366123 | 0.040871 | 0.050282 | 1.897417 | 1.899068 | 0.015821 | 0.021165 |
| 100 | 8.161291 | 8.196691 | 0.517249 | 0.077239 | 2.114292 | 2.123503 | 0.174330 | 0.024947 |
| 110 | 8.993875 | 9.023868 | 0.319884 | 0.093865 | 2.327458 | 2.337916 | 0.109838 | 0.028324 |
| 120 | 9.781104 | 9.786512 | 0.052223 | 0.052793 | 2.546501 | 2.548840 | 0.025315 | 0.028781 |
| 130 | 10.605292 | 10.629249 | 0.520515 | 0.094771 | 2.750896 | 2.757321 | 0.112339 | 0.036626 |
| 140 | 11.373396 | 11.447371 | 0.599175 | 0.103594 | 2.993187 | 3.011823 | 0.092967 | 0.051459 |
| 150 | 12.328583 | 12.413116 | 0.452310 | 0.145355 | 3.198625 | 3.224419 | 0.131319 | 0.064917 |


Ordinary least squares, equal weight per size, model `median_ms = a*n + b`:

```text
Current: slope=0.081136505 ms/n; intercept=0.065862434 ms; R²=0.999943167
Residuals (n: ms): 0: +0.016158, 10: +0.008105, 20: +0.005221, 30: +0.005730, 40: -0.014572, 50: -0.000625, 60: -0.004574, 70: +0.000666, 80: -0.006761, 90: -0.005336, 100: -0.018222, 110: +0.002997, 120: -0.021139, 130: -0.008316, 140: -0.051577, 150: +0.092245
Max absolute residual: 0.092245 ms

cek: slope=0.021148022 ms/n; intercept=0.009985647 ms; R²=0.999897027
Residuals (n: ms): 0: +0.010514, 10: +0.007659, 20: +0.005263, 30: -0.000551, 40: -0.002970, 50: +0.000447, 60: -0.005055, 70: -0.005931, 80: -0.003515, 90: -0.015890, 100: -0.010496, 110: -0.008810, 120: -0.001247, 130: -0.008332, 140: +0.022479, 150: +0.016436
Max absolute residual: 0.022479 ms

Old comparison: n, Current change %, CEK change %
10 +4.53% +1.38%
20 +4.95% +2.15%
50 +4.15% +3.87%
100 +2.57% +1.84%
150 +4.27% +2.32%
```

## Interpretation and limitations

Both evaluators are **approximately linear over the measured range 0–150**.
Current's maximum absolute residual is 0.092245 ms at n=150 (0.75% of that
median); CEK's is 0.022479 ms at n=140 (0.75%). Current residuals fluctuate
around zero without sustained accelerating growth. CEK residuals show a small
bow (positive at the ends and mostly negative in the middle), but remain small
in absolute units. The linear model is a reasonable description at this
measurement resolution; it is not an exact law or proof of asymptotic complexity.

Some individual samples have long upper tails: Current SD at n=100 is
0.517249 ms versus IQR 0.077239 ms; at n=140 SD is 0.599175 ms versus IQR
0.103594 ms. CEK also has occasional larger samples (n=100 SD 0.174330 ms
versus IQR 0.024947 ms). Means, SDs, IQRs and all raw samples are retained,
rather than deleting outliers or inventing their cause. No clear nonlinear
execution boundary is demonstrated.

Separate counters remain exactly linear at every size: Current root and beta
reductions and CEK closure applications/environment extensions each equal
`6 + 7n`; Current shift visits `18 + 17n`, substitution visits `32 + 30n`;
CEK transitions `31 + 35n`, lookups `3 + 8n`. Each CEK application-frame count
is `6 + 7n`; maximum continuation depth is 2; Builtin applications are 0.
These counts support the workload interpretation but do not equate evaluator
operations or prove identical semantics.

Compared with the historical medians at 10, 20, 50, 100 and 150, Current is
2.57–4.95% higher and CEK 1.38–3.87% higher. There is no large unexplained
discrepancy. Different sessions, sample counts and runtime conditions prevent
exact equality; the cause of the small shift was not isolated.

A category axis gives unequal numeric intervals equal visual spacing. For the
old sizes 1, 2, 5, 10, 20, 50, 100, 150, that presentation distorts the slope
and can make a linear relationship look nonlinear. **If the old slide used
that axis, its spacing was misleading.** The slide/plot is not present in this
repository, so its actual axis configuration could not be independently
verified. No new graph is generated; regressions use true numeric n values.

Limitations: one machine, one session, one tail-recursive workload, warm caches,
fixed ascending size order and Current-first pairing; no randomization, thermal
controls, cold preparation timing or cross-machine replication. High R² does
not establish mathematical asymptotic complexity, universal CEK superiority,
or semantic equivalence between Current rewriting and strict CBV. The known
historical preparation failure at n=200 was not retested or bypassed.
No evaluator or workload issue requiring a fix was found; no Milestone 4 work
was started.

## Verification

- Recursion tests: 10 passed (including configurable sample count and invalid settings).
- All `experiments/cek_machine` tests: 43 passed.
- Default project suite: 577 passed, 4 slow tests deselected (6.49s).
  The four slow examples were not rerun for this benchmark-only change.
- Raw data checked for all 16 sizes, 500 positive samples per evaluator per size,
  recomputed statistics, and the exact counter formulae above.
- Analysis coefficients and residual calculations cross-checked against the
  OLS normal equations; `git diff --check` and Python compilation passed.
- Protected files compared byte-for-byte against the base via `git diff`:
  dsl.py, cbv_cek.py, benchmark.py, metrics.py and historical results unchanged.
