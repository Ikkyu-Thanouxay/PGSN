"""Minimal strict CBV CEK experiment; no production evaluator fallback.

Only initial_state performs name removal. step operates on nameless syntax,
with evaluated values in environments and pending work in explicit frames.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from pgsn.pgsn_term import (
    Abs, App, Boolean, Constant, Div, Integer, Minus, Mod, Plus, String,
    Term, Times, Variable,
)

Primitive: TypeAlias = Integer | String | Boolean | Constant
Arithmetic: TypeAlias = Plus | Minus | Times | Div | Mod
PRIMITIVES = (Integer, String, Boolean, Constant)
ARITHMETIC = (Plus, Minus, Times, Div, Mod)


class UnsupportedTermError(TypeError):
    """The experimental machine does not implement this syntax."""


@dataclass(frozen=True)
class Closure:
    body: Term
    env: Environment


@dataclass(frozen=True)
class PartialBuiltin:
    builtin: Arithmetic
    args: tuple[RuntimeValue, ...] = ()


RuntimeValue: TypeAlias = Primitive | Closure | PartialBuiltin
Environment: TypeAlias = tuple[RuntimeValue, ...]


@dataclass(frozen=True)
class Halt:
    pass


@dataclass(frozen=True)
class AppFunction:
    argument: Term
    env: Environment
    continuation: Continuation


@dataclass(frozen=True)
class AppArgument:
    function: RuntimeValue
    continuation: Continuation


Continuation: TypeAlias = Halt | AppFunction | AppArgument


def is_value(control: Term | RuntimeValue) -> bool:
    return type(control) in PRIMITIVES or isinstance(control, (Closure, PartialBuiltin))


@dataclass(frozen=True)
class State:
    control: Term | RuntimeValue
    environment: Environment = ()
    continuation: Continuation = Halt()

    @property
    def halted(self) -> bool:
        return is_value(self.control) and isinstance(self.continuation, Halt)


def initial_state(term: Term) -> State:
    return State(term.remove_name() if term.is_named else term)


def step(state: State) -> State:
    """Perform one transition; a completed state is a fixed point.

    Callers constructing states directly must supply nameless syntax and
    value-only environments, as produced by initial_state and this function.
    """
    control, env, k = state.control, state.environment, state.continuation
    if is_value(control):
        if isinstance(k, Halt):
            return state
        if isinstance(k, AppFunction):
            return State(k.argument, k.env, AppArgument(control, k.continuation))
        if not isinstance(k, AppArgument):
            raise TypeError('Invalid continuation')
        function = k.function
        if isinstance(function, Closure):
            return State(function.body, (control,) + function.env, k.continuation)
        if isinstance(function, PartialBuiltin):
            args = function.args + (control,)
            if len(args) < function.builtin.arity:
                return State(PartialBuiltin(function.builtin, args), (), k.continuation)
            if not all(type(arg) is Integer for arg in args):
                raise TypeError('Arithmetic requires Integer values')
            if not function.builtin.applicable_args(args):
                raise TypeError('Invalid arithmetic arguments')
            result, rest = function.builtin.apply_args(args)
            if rest or type(result) is not Integer:
                raise TypeError('Unexpected arithmetic result')
            return State(result, (), k.continuation)
        raise TypeError(f'Cannot apply non-function value: {type(function).__name__}')
    if isinstance(control, Variable):
        if control.num is None or not 0 <= control.num < len(env):
            raise LookupError('Unbound de Bruijn variable')
        return State(env[control.num], env, k)
    if isinstance(control, Abs):
        return State(Closure(control.t, env), env, k)
    if isinstance(control, App):
        return State(control.t1, env, AppFunction(control.t2, env, k))
    if type(control) in ARITHMETIC:
        return State(PartialBuiltin(control), env, k)
    raise UnsupportedTermError(f'Unsupported CEK term: {type(control).__name__}')


def evaluate(term: Term) -> RuntimeValue:
    """Evaluate using an iterative transition loop, returning a runtime value."""
    state = initial_state(term)
    while not state.halted:
        state = step(state)
    return state.control
