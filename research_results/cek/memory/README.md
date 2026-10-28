# Memory results: start with the full cold run

For readable tables, open the [main results workbook](../../PGSN_Research_Results.xlsx)
and choose `Memory` or `Memory Chart`. For timing, return to the
[CEK evidence guide](../README.md); these memory observations do not measure time.

| Folder | What it contains | Where to start |
|---|---|---|
| `2026-10-28_identity_captured_cold_full_01/` | Main cold-memory experiment: Identity and Captured at n=10,100,200; ten observations per evaluator/control per configuration, 180 observations total | [Report](2026-10-28_identity_captured_cold_full_01/README.md), [summary](2026-10-28_identity_captured_cold_full_01/summary.csv), [raw observations](2026-10-28_identity_captured_cold_full_01/raw_samples.csv), [metadata](2026-10-28_identity_captured_cold_full_01/metadata.json) |
| `2026-10-28_identity_n10_pilot_01/` | Earlier methodology pilot: one Identity n=10 observation per evaluator and one control; not a repeated-run estimate | [Report](2026-10-28_identity_n10_pilot_01/README.md), [raw observations](2026-10-28_identity_n10_pilot_01/raw_samples.csv), [metadata and source hashes](2026-10-28_identity_n10_pilot_01/metadata.json) |

Memory values are **bytes of traced live Python blocks**, not total RAM or RSS
(resident process memory). Peak growth is peak minus the prepared-input
baseline. Ending growth is ending live bytes minus baseline, with the result
retained. Neither metric is cumulative allocation volume; ending growth alone
does not demonstrate a leak. Cold means the first evaluator call on a freshly
prepared term, without evaluator warmups, in a fresh interpreter. Controls are
shown separately and are not subtracted.

Use the [reviewed PNG](2026-10-28_identity_captured_cold_full_01/peak_growth_reviewed.png)
or [reviewed SVG](2026-10-28_identity_captured_cold_full_01/peak_growth_reviewed.svg).
The original figures clipped the Captured CEK n=200 point. The reviewed figures
correct the shared-axis limit without changing observations or summaries.
All figures remain unchanged in their original locations.

Inside each run, `raw_samples.csv` provides tabular observations;
`raw_samples.json` and worker JSON retain additional measurement/environment
details. `summary.csv` in the full run contains derived statistics;
`validation.json` records saved-data checks. `metadata.json` records the original
command, environment, source checkpoint and hashes. These names describe their
roles within each dated experiment and are deliberately preserved.

`README_initial.md`, `analysis_metadata_initial.json`, the original figures and
`render_reviewed_plot.py` preserve the plot-review history. Keep them, along with
the pilot and CSV/JSON pairs. See the [cleanup review](../../cleanup_review.md).

The [manifest](../../manifest.csv) covers the earlier timing/profiling datasets
and predates these memory runs. For these runs, use the linked metadata rather
than interpreting the manifest's omission as missing evidence.
