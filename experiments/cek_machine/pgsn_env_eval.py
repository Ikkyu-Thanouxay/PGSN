from __future__ import annotations

from typing import TypeAlias

from attrs import frozen

from pgsn.pgsn_term import Abs, App, Boolean, Constant, Integer, String, Term, Variable


Environment: TypeAlias = "tuple[DelayedArgument, ...]"


@frozen
class DelayedArgument:
    term: Term
    env: Environment


@frozen
class Closure:
    body: Term
    env: Environment


def lookup_variable(variable: Variable, env: Environment) -> DelayedArgument:
    assert not variable.is_named
    assert variable.num is not None
    return env[variable.num]


def make_closure(abs_term: Abs, env: Environment) -> Closure:
    assert not abs_term.is_named
    return Closure(body=abs_term.t, env=env)


RuntimeValue: TypeAlias = "Term | Closure"


def eval_env(term: Term, env: Environment = ()) -> RuntimeValue:
    if term.is_named:
        term = term.remove_name()

    if isinstance(term, (Integer, String, Boolean, Constant)):
        return term

    if isinstance(term, Variable):
        delayed = lookup_variable(term, env)
        return eval_env(delayed.term, delayed.env)

    if isinstance(term, Abs):
        return make_closure(term, env)

    if isinstance(term, App):
        fn = eval_env(term.t1, env)

        if not isinstance(fn, Closure):
            raise TypeError(f"Cannot apply non-closure: {fn}")

        delayed_arg = DelayedArgument(
            term=term.t2,
            env=env,
        )

        body_env = (delayed_arg,) + fn.env
        return eval_env(fn.body, body_env)

    raise TypeError(f"Unsupported term in environment evaluator: {term}")
