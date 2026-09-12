# PGSN Environment Evaluator Research Instructions

## Research Goal

Investigate whether the environment-based evaluator can reduce the
shift/subst traversal cost of the current PGSN evaluator while preserving
the current evaluator's behavior.

This is research code. Correctness, reproducibility, and clear evidence are
more important than adding many features quickly.

## Current Research State

Main prototype:
`experiments/cek_machine/pgsn_env_eval.py`

Comparison tests:
`experiments/cek_machine/test_pgsn_env_eval.py`

Benchmark:
`experiments/cek_machine/benchmark_pgsn_env_eval.py`

Research log:
`docs/research_log.md`

The prototype currently uses:
- Environment
- Closure
- DelayedArgument
- BuiltinClosure
- explicit current Term / control
- explicit Environment
- Python call stack instead of an explicit continuation K

This is CEK-inspired environment-based evaluation, not a complete CEK
machine.

Already tested:
- basic lambda application
- captured variables
- functions passed as arguments
- unused delayed arguments
- delayed arguments evaluated when needed
- deep synthetic captured-variable workload
- plus, minus, times, div
- Builtin argument from Environment
- Builtin passed as a function

## General Workflow

Before making changes:
1. inspect the current implementation, tests, research log, and git history
2. run the focused environment-evaluator tests
3. run the full repository test suite
4. record the starting state

Work incrementally.

For each unsupported feature:
1. identify exactly why the selected real Python PGSN example cannot run
2. add only the smallest necessary support
3. add focused tests
4. compare the current evaluator and environment evaluator
5. verify the final result matches
6. verify relevant evaluation-order behavior
7. run focused tests
8. run the full test suite at stable checkpoints
9. update the research log
10. commit a coherent working checkpoint

Do not modify the current evaluator merely to make the prototype agree.

Do not weaken tests.

Unexpected differences are research findings. Investigate and record them.

## Evaluation Behavior

Preserve the current PGSN evaluator's behavior.

In particular:
- unused arguments must not be evaluated merely because they were passed
- needed delayed arguments must be evaluated when required
- variable scoping and captured variables must match
- Builtin argument behavior must match
- errors must not silently become successful results

For each newly supported behavior, prefer comparison tests that exercise both
evaluators rather than testing only the prototype.

## Git Rules

Work only on the current research branch.

Use small, meaningful commits.

Before each code commit:
- relevant focused tests must pass
- do not knowingly commit broken code

Good checkpoint examples:
- document the unsupported Terms blocking one Python example
- add support for one related Term/value family with tests
- add support for one related Builtin family with tests
- make one existing Python PGSN example run end-to-end
- record the result of one completed experiment

If an implementation attempt fails:
- record what was attempted
- record the observed failure
- record the likely cause
- revert the broken implementation if necessary
- keep useful research notes even if the code is rejected

Push stable checkpoint commits to origin.

## Research Record

Keep `docs/research_log.md` updated.

For important checkpoints record:
- goal
- files/code inspected
- change made
- tests run
- observed result
- unexpected problem
- cause, if known
- solution
- what the result proves
- what it does not prove
- next step
- relevant commit SHA

Do not delete or overwrite previous experiment results.

## Performance Rules

Correctness comes before performance.

Do not repeatedly run expensive benchmarks unless they answer the current
research question.

Do not claim that synthetic benchmark speedups apply to full PGSN.

Do not claim that PGSN has quadratic complexity based on the synthetic
nested-lambda test.

## Current Milestone

The current milestone ends when the environment evaluator can evaluate at
least one existing representative PGSN program written in a `.py` file
end-to-end and its result matches the current evaluator.

Start with the smallest useful existing Python PGSN example.

Only implement features required to reach this milestone.

Do not:
- continue into XML evaluation
- benchmark SolarWinds
- try to complete every PGSN feature
- implement explicit K only for theoretical completeness unless it becomes
  necessary for correctness

## Stop Condition

Stop immediately once:
- at least one representative existing `.py` PGSN example runs end-to-end
  with the environment evaluator
- its result matches the current evaluator
- focused tests pass
- the full repository test suite passes
- the research log is updated
- a final stable checkpoint commit is made and pushed
- the working tree is clean

Then provide a handoff containing:
- starting commit
- ending commit
- commits created, in order
- files changed
- PGSN features added
- tests and exact results
- selected `.py` example
- exact reproduction command
- failed attempts and their causes
- solutions applied
- remaining unsupported features
- what the result proves
- what it does not prove
- recommended next research step

Do not proceed to XML until the user reviews the handoff.
