"""
Mini CEK machine experiment.

This file is NOT the real PGSN evaluator.
It is only a small learning prototype.

Goal:
- understand the difference between substitution-based evaluation
  and CEK-machine evaluation
- later compare this idea with PGSN's current fully_eval()
"""

# We will implement this slowly.
# First target:
#   ((lambda x. x) "hello")  ==> "hello"