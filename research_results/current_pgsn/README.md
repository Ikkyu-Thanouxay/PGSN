# Current-PGSN real-example measurements

The canonical fresh dataset is
[2026-10-19_current_pgsn_examples](runs/2026-10-19_current_pgsn_examples/README.md).
It retains 29 pilots, 1,142 measured clean samples and 115 warmups. All 24 XML
programs and four Python inputs have successful complete-pipeline measurements.
All 17 XML modules are metadata-only; seven Python files are not safely
benchmarkable, and SolarWinds.py has a retained GSN conversion error.

The dataset separates clean load/compile, fully_eval, GSN conversion, textual
output, worker pipeline total and parent process-wall samples. Counters and
cProfile run in separate fresh processes with separate diagnostic fields.
The run README and metadata record source/harness commit, environment,
repetition policy, statuses and limitations, including an observed clock-span
discrepancy. Future runs must use fresh directories and retain this separation.

Historical pre-free_bound profiling remains under ../historical/ and must not
be confused with these optimized current-PGSN measurements. No complete-program
CEK comparison is implied. No historical or existing CEK result was overwritten.
