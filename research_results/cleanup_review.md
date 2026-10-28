# Cleanup review — no removals made

The workbook remains the main reading file. Evidence, figures and dated run
folders are retained at their existing paths. No file has been established as
an exact duplicate with neither unique information nor references.

## Possible housekeeping candidates, for review only

These existing, untracked/ignored macOS Finder metadata files store folder-view
settings rather than research measurements. They are not part of the Git
commit. Removing them could reset Finder presentation and is not necessary for
reading the results; they have not been removed:

- `research_results/.DS_Store`
- `research_results/current_pgsn/.DS_Store`
- `research_results/current_pgsn/runs/.DS_Store`
- `research_results/current_pgsn/runs/2026-10-19_current_pgsn_examples/.DS_Store`

## Apparent duplicates that should be preserved

- In `cek/memory/2026-10-28_identity_captured_cold_full_01/`, `README_initial.md`
  and `analysis_metadata_initial.json` record the initial plot/report state.
  The initial and reviewed PNG/SVG figures document the clipping correction;
  `render_reviewed_plot.py` reproduces it. Superseded presentation does not make
  these records disposable.
- `raw_samples.csv` / `raw_samples.json`, `pilot.csv` / `pilot.json`, and
  `counters.csv` / `counters.json` overlap in values but serve different reading
  and metadata needs. JSON can retain nested worker/environment details absent
  from the CSV view. No pair is approved for removal.
- The one-observation memory pilot has its own methodology, source checkpoint
  and metadata; the full run does not replace that evidence.
- Historical before/after output pairs can be byte-identical by design. Both
  sides document the comparison and have references; keep both.
- Profiler text and JSON provide human-readable and structured diagnostic
  views. Instrumented diagnostics are distinct from clean timing samples.

Review removals separately; this update makes none.
