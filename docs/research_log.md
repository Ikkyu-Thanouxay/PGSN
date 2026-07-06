# PGSN Research Log

## 2026-06-25: Profiler investigation

### Task
Add profiling support to PGSN and identify slow parts.

### Result
XML loading and tree output were not the main bottleneck.

The main bottleneck was evaluation, especially:
- fully_eval
- shift_or_none
- subst_or_none
- reduce_or_none

### Interpretation
PGSN terms are lambda-calculus-like. Current evaluation uses substitution.
Substitution causes many recursive traversals and many shift operations.

### Next task from professor
Study CEK / CESK machines and consider whether PGSN can be evaluated faster using an abstract machine or bytecode.