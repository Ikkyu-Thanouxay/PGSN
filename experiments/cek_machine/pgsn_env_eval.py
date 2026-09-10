from __future__ import annotations

from typing import TypeAlias

from attrs import frozen

from pgsn.pgsn_term import (
    Abs,
    App,
    Boolean,
    Builtin,
    Constant,
    Div,
    Integer,
    Minus,
    Plus,
    String,
    Term,
    Times,
    Variable,
)


Environment: TypeAlias = "tuple[DelayedArgument, ...]"

_environment_lookup_count = 0
_closure_creation_count = 0
_delayed_argument_creation_count = 0
_delayed_argument_evaluation_count = 0
_metrics_enabled = True


def set_metrics_enabled(enabled: bool) -> None:
    global _metrics_enabled
    _metrics_enabled = enabled


def reset_environment_lookup_count() -> None:
    global _environment_lookup_count
    _environment_lookup_count = 0


def get_environment_lookup_count() -> int:
    return _environment_lookup_count


def reset_closure_creation_count() -> None:
    global _closure_creation_count
    _closure_creation_count = 0


def get_closure_creation_count() -> int:
    return _closure_creation_count


def reset_delayed_argument_creation_count() -> None:
    global _delayed_argument_creation_count
    _delayed_argument_creation_count = 0


def get_delayed_argument_creation_count() -> int:
    return _delayed_argument_creation_count


def reset_delayed_argument_evaluation_count() -> None:
    global _delayed_argument_evaluation_count
    _delayed_argument_evaluation_count = 0


def get_delayed_argument_evaluation_count() -> int:
    return _delayed_argument_evaluation_count


@frozen
class DelayedArgument:
    term: Term
    env: Environment


@frozen
class Closure:
    body: Term
    env: Environment


@frozen
class BuiltinClosure:
    builtin: Builtin
    args: tuple[DelayedArgument, ...] = ()


def lookup_variable(variable: Variable, env: Environment) -> DelayedArgument:
    global _environment_lookup_count
    if _metrics_enabled:
        _environment_lookup_count += 1

    assert not variable.is_named
    assert variable.num is not None
    return env[variable.num]


def make_closure(abs_term: Abs, env: Environment) -> Closure:
    global _closure_creation_count
    if _metrics_enabled:
        _closure_creation_count += 1

    assert not abs_term.is_named
    return Closure(body=abs_term.t, env=env)


RuntimeValue: TypeAlias = "Term | Closure | BuiltinClosure"


def eval_env(term: Term, env: Environment = ()) -> RuntimeValue:
    global _delayed_argument_creation_count
    global _delayed_argument_evaluation_count

    if term.is_named:
        term = term.remove_name()

    if isinstance(term, (Integer, String, Boolean, Constant)):
        return term

    if isinstance(term, (Plus, Minus, Times, Div)):
        return BuiltinClosure(builtin=term)

    if isinstance(term, Variable):
        delayed = lookup_variable(term, env)

        if _metrics_enabled:
            _delayed_argument_evaluation_count += 1

        return eval_env(delayed.term, delayed.env)

    if isinstance(term, Abs):
        return make_closure(term, env)

    if isinstance(term, App):
        fn = eval_env(term.t1, env)

        if _metrics_enabled:
            _delayed_argument_creation_count += 1

        delayed_arg = DelayedArgument(
            term=term.t2,
            env=env,
        )

        if isinstance(fn, Closure):
            body_env = (delayed_arg,) + fn.env
            return eval_env(fn.body, body_env)

        if isinstance(fn, BuiltinClosure):
            args = fn.args + (delayed_arg,)

            # Partial application: wait until the Builtin has enough arguments.
            if len(args) < fn.builtin.arity:
                return BuiltinClosure(
                    builtin=fn.builtin,
                    args=args,
                )

            evaluated_args = []

            for arg in args:
                if _metrics_enabled:
                    _delayed_argument_evaluation_count += 1

                value = eval_env(arg.term, arg.env)

                if not isinstance(value, Term):
                    raise TypeError(
                        f"Builtin argument did not evaluate to a Term: {value}"
                    )

                evaluated_args.append(value)

            evaluated_args = tuple(evaluated_args)

            if not fn.builtin.applicable_args(evaluated_args):
                raise TypeError(
                    f"Builtin cannot accept arguments: "
                    f"{fn.builtin}, {evaluated_args}"
                )

            result, rest = fn.builtin.apply_args(evaluated_args)

            if rest:
                raise TypeError(
                    f"Unexpected remaining Builtin arguments: {rest}"
                )

            return eval_env(result)

        raise TypeError(f"Cannot apply non-function value: {fn}")

    raise TypeError(f"Unsupported term in environment evaluator: {term}")
