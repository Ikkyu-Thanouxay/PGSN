# Traced-memory methodology pilot

Exactly one Identity n=10 observation per evaluator and a no-evaluation control.
All memory values are bytes. baseline is measured after preparation and GC;
peak is reset immediately before one call; ending is read with result alive.
Peak growth = peak - baseline; end growth = ending - baseline.
These describe traced live Python blocks, not RSS, cumulative allocations,
or a general evaluator ranking. The control is not subtracted automatically.
Source/command/environment and limitations are retained in metadata/raw JSON.
Run the coordinator with --verify-only --output this-directory to check saved data.
