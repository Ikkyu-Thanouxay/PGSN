"""Minimal strict CBV CEK experiment; no production evaluator fallback.

Only initial_state performs name removal. step operates on nameless syntax,
with evaluated values in environments and pending work in explicit frames.

Basic records evaluate every field once, in source insertion order, before
becoming values (including before lookup). Fields must produce primitive values;
closures, partial builtins and nested records are outside this milestone.
RecordValue is experimental runtime data, not a production Record Term. There
is no automatic readback, record merging, keyword/default or object support.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from pgsn.pgsn_term import (
    Abs, App, Boolean, Constant, Div, Integer, Minus, Mod, Plus, Record, String,
    Term, Times, Variable,
)

Primitive: TypeAlias = Integer | String | Boolean | Constant
Arithmetic: TypeAlias = Plus | Minus | Times | Div | Mod
PRIMITIVES = (Integer, String, Boolean, Constant)
ARITHMETIC = (Plus, Minus, Times, Div, Mod)


class UnsupportedTermError(TypeError):
    """The experimental machine does not implement this syntax."""


class ExperimentalStuckError(TypeError):
    """Unsupported stuck state; final PGSN semantics require term readback."""


@dataclass(frozen=True)
class Closure:
    body: Term
    env: Environment


@dataclass(frozen=True)
class PartialBuiltin:
    builtin: Arithmetic
    args: tuple[RuntimeValue, ...] = ()


@dataclass(frozen=True)
class RecordValue:
    """Evaluated string-labelled primitive fields, retaining insertion order."""

    fields: tuple[tuple[str, Primitive], ...]


RuntimeValue: TypeAlias = Primitive | Closure | PartialBuiltin | RecordValue
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


@dataclass(frozen=True)
class RecordField:
    """Finish one field, then evaluate the remaining fields in their lexical env."""

    label: str
    remaining: tuple[tuple[str, Term], ...]
    completed: tuple[tuple[str, Primitive], ...]
    env: Environment
    continuation: Continuation


Continuation: TypeAlias = Halt | AppFunction | AppArgument | RecordField


def is_value(control: Term | RuntimeValue) -> bool:
    return type(control) in PRIMITIVES or isinstance(control, (Closure, PartialBuiltin, RecordValue))


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
        if isinstance(k, RecordField):
            if type(control) not in PRIMITIVES:
                raise UnsupportedTermError(
                    f'Record field {k.label!r} must evaluate to Integer, String, '
                    f'Boolean or Constant; got {type(control).__name__}')
            completed = k.completed + ((k.label, control),)
            if k.remaining:
                (label, term), *rest = k.remaining
                return State(term, k.env,
                             RecordField(label, tuple(rest), completed, k.env, k.continuation))
            return State(RecordValue(completed), k.env, k.continuation)
        if isinstance(k, AppFunction):
            return State(k.argument, k.env, AppArgument(control, k.continuation))
        if not isinstance(k, AppArgument):
            raise TypeError('Invalid continuation')
        function = k.function
        if isinstance(function, Closure):
            return State(function.body, (control,) + function.env, k.continuation)
        if isinstance(function, RecordValue):
            if type(control) is not String:
                raise TypeError('Record lookup requires a String key')
            for label, value in function.fields:
                if label == control.value:
                    return State(value, (), k.continuation)
            raise KeyError(f'Unknown record field {control.value!r}')
        if isinstance(function, PartialBuiltin):
            args = function.args + (control,)
            if len(args) < function.builtin.arity:
                return State(PartialBuiltin(function.builtin, args), (), k.continuation)
            if not all(type(arg) is Integer for arg in args):
                raise ExperimentalStuckError('Arithmetic requires Integer values')
            applied = function.builtin.apply_args_or_none(args)
            if applied is None:
                raise ExperimentalStuckError('Arithmetic builtin cannot reduce')
            result, rest = applied
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
    if isinstance(control, Record):
        fields = tuple(control.attributes().items())
        if not fields:
            return State(RecordValue(()), env, k)
        (label, term), *rest = fields
        return State(term, env, RecordField(label, tuple(rest), (), env, k))
    if type(control) in ARITHMETIC:
        return State(PartialBuiltin(control), env, k)
    raise UnsupportedTermError(f'Unsupported CEK term: {type(control).__name__}')


def evaluate(term: Term) -> RuntimeValue:
    """Evaluate using an iterative transition loop, returning a runtime value."""
    state = initial_state(term)
    while not state.halted:
        state = step(state)
    return state.control
