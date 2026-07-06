from __future__ import annotations

from typing import TypeAlias

from attrs import define


Expr: TypeAlias = "Const | Var | Abs | App | Add"
Value: TypeAlias = "Const | Abs | Closure"
Env: TypeAlias = "dict[str, Value]"
Frame: TypeAlias = "ArgFrame | FunFrame | AddLeftFrame | AddRightFrame"


@define(frozen=True)
class Const:
    value: object


@define(frozen=True)
class Var:
    name: str


@define(frozen=True)
class Abs:
    param: str
    body: Expr


@define(frozen=True)
class App:
    fn: Expr
    arg: Expr


@define(frozen=True)
class Add:
    left: Expr
    right: Expr


def subst(term: Expr, name: str, value: Value) -> Expr:
    if isinstance(term, Const):
        return term

    if isinstance(term, Var):
        if term.name == name:
            return value
        return term

    if isinstance(term, Abs):
        if term.param == name:
            return term
        return Abs(term.param, subst(term.body, name, value))

    if isinstance(term, App):
        return App(subst(term.fn, name, value), subst(term.arg, name, value))

    if isinstance(term, Add):
        return Add(subst(term.left, name, value), subst(term.right, name, value))

    raise TypeError(f"Unknown term: {term}")


def eval_subst(term: Expr) -> Value:
    if isinstance(term, Const):
        return term

    if isinstance(term, Var):
        raise NameError(f"Free variable: {term.name}")

    if isinstance(term, Abs):
        return term
    
    if isinstance(term, Add):
        left = eval_subst(term.left)
        right = eval_subst(term.right)

        if not isinstance(left, Const) or not isinstance(right, Const):
            raise TypeError("Add expects constants")

        return Const(left.value + right.value)

    if isinstance(term, App):
        fn_value = eval_subst(term.fn)
        arg_value = eval_subst(term.arg)

        if not isinstance(fn_value, Abs):
            raise TypeError(f"Cannot apply non-abstraction: {fn_value}")

        body = subst(fn_value.body, fn_value.param, arg_value)
        return eval_subst(body)

    raise TypeError(f"Unknown term: {term}")


@define(frozen=True)
class Closure:
    param: str
    body: Expr
    env: Env


@define(frozen=True)
class ArgFrame:
    arg: Expr
    env: Env


@define(frozen=True)
class FunFrame:
    fn: Value


@define(frozen=True)
class AddLeftFrame:
    right: Expr
    env: Env


@define(frozen=True)
class AddRightFrame:
    left: Value


def eval_cek(term: Expr) -> Value:
    control: Expr = term
    env: Env = {}
    kont: list[Frame] = []

    value: Value | None = None
    mode = "expr"

    while True:
        if mode == "expr":
            if isinstance(control, Const):
                value = control
                mode = "value"
                continue

            if isinstance(control, Var):
                value = env[control.name]
                mode = "value"
                continue

            if isinstance(control, Abs):
                value = Closure(control.param, control.body, env.copy())
                mode = "value"
                continue

            if isinstance(control, App):
                kont.append(ArgFrame(control.arg, env.copy()))
                control = control.fn
                continue

            if isinstance(control, Add):
                kont.append(AddLeftFrame(control.right, env.copy()))
                control = control.left
                continue

            raise TypeError(f"Unknown control: {control}")

        if mode == "value":
            if value is None:
                raise RuntimeError("CEK machine entered value mode without a value")

            if not kont:
                return value

            frame = kont.pop()

            if isinstance(frame, ArgFrame):
                kont.append(FunFrame(value))
                control = frame.arg
                env = frame.env
                mode = "expr"
                continue

            if isinstance(frame, FunFrame):
                if not isinstance(frame.fn, Closure):
                    raise TypeError(f"Cannot apply non-closure: {frame.fn}")

                env = frame.fn.env.copy()
                env[frame.fn.param] = value
                control = frame.fn.body
                mode = "expr"
                continue

            if isinstance(frame, AddLeftFrame):
                kont.append(AddRightFrame(value))
                control = frame.right
                env = frame.env
                mode = "expr"
                continue

            if isinstance(frame, AddRightFrame):
                if not isinstance(frame.left, Const) or not isinstance(value, Const):
                    raise TypeError("Add expects constants")

                value = Const(frame.left.value + value.value)
                mode = "value"
                continue

            raise TypeError(f"Unknown frame: {frame}")

        raise RuntimeError(f"Unknown mode: {mode}")


def run_example(name: str, term: Expr) -> None:
    print(f"\n{name}")
    print("-" * len(name))
    print(f"term: {term}")
    print(f"subst: {eval_subst(term)}")
    print(f"cek:   {eval_cek(term)}")


def main() -> None:
    identity = App(
        Abs("x", Var("x")),
        Const("hello"),
    )

    nested = App(
        App(
            Abs("x", Abs("y", Var("x"))),
            Const("A"),
        ),
        Const("B"),
    )

    duplicated = App(
        Abs("x", Add(Var("x"), Var("x"))),
        Add(Const(1), Const(2)),
    )

    run_example("identity", identity)
    run_example("nested lambda", nested)
    run_example("duplicated variable", duplicated)


if __name__ == "__main__":
    main()