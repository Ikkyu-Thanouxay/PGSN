# Profiler Report: 2026-06-25

This folder contains raw profiler outputs from the PGSN profiling task.

## Files

- `raw/profile_gsn.txt`
- `raw/profile_gsn_time.txt`
- `raw/profile_map_term.txt`
- `raw/profile_map_term_time.txt`
- `raw/profile_robot.txt`
- `raw/profile_robot_time.txt`
- `raw/profile_cap_a.txt`
- `raw/profile_cap_a_time.txt`
- `raw/profile_solarwinds.txt`
- `raw/profile_solarwinds_time.txt`

## Main finding

The slow part is not XML parsing or GSN tree output.
The slow part is repeated term evaluation.

The suspected cause is substitution-based lambda evaluation:
- many calls to `subst_or_none`
- many calls to `shift_or_none`
- repeated traversal/rebuilding of terms

## Next idea

Try a CEK-machine-style evaluator to avoid substitution by using environments and closures.