from pgsn.pgsn_term import Abs, App, Integer, Variable

from pgsn_env_eval import eval_env


def compare_results(name, expression, term, expected):
    current_result = term.fully_eval()
    env_result = eval_env(term)

    current_value = current_result.value
    env_value = env_result.value

    print()
    print(f"=== {name} ===")
    print(f"Expression:            {expression}")
    print(f"Expected result:       {expected}")
    print(f"Current evaluator:     {current_value}")
    print(f"Environment evaluator: {env_value}")
    print(f"Same result:           {'YES' if current_value == env_value else 'NO'}")

    assert current_value == expected
    assert env_value == expected
    assert env_value == current_value


def test_identity():
    x = Variable.from_name("x")

    identity = Abs.named(
        v=x,
        t=x,
    )

    term = App.term(
        identity,
        Integer.named(value=5),
    )

    compare_results(
        name="Identity",
        expression="(λx. x) 5",
        term=term,
        expected=5,
    )


def test_constant_function():
    x = Variable.from_name("x")

    constant_function = Abs.named(
        v=x,
        t=Integer.named(value=1),
    )

    term = App.term(
        constant_function,
        Integer.named(value=5),
    )

    compare_results(
        name="Constant function",
        expression="(λx. 1) 5",
        term=term,
        expected=1,
    )


def test_captured_variable():
    x = Variable.from_name("x")
    y = Variable.from_name("y")

    inner = Abs.named(
        v=y,
        t=x,
    )

    outer = Abs.named(
        v=x,
        t=inner,
    )

    term = App.term(
        App.term(
            outer,
            Integer.named(value=5),
        ),
        Integer.named(value=10),
    )

    compare_results(
        name="Captured variable",
        expression="((λx. λy. x) 5) 10",
        term=term,
        expected=5,
    )


def test_function_argument():
    f = Variable.from_name("f")
    x = Variable.from_name("x")

    identity = Abs.named(
        v=x,
        t=x,
    )

    apply_f_to_5 = Abs.named(
        v=f,
        t=App.term(
            f,
            Integer.named(value=5),
        ),
    )

    term = App.term(
        apply_f_to_5,
        identity,
    )

    compare_results(
        name="Function argument",
        expression="(λf. f 5) (λx. x)",
        term=term,
        expected=5,
    )


def test_unused_argument():
    x = Variable.from_name("x")

    constant_function = Abs.named(
        v=x,
        t=Integer.named(value=1),
    )

    invalid_argument = App.term(
        Integer.named(value=1),
        Integer.named(value=2),
    )

    term = App.term(
        constant_function,
        invalid_argument,
    )

    compare_results(
        name="Unused argument",
        expression="(λx. 1) (1 2)",
        term=term,
        expected=1,
    )


def test_used_delayed_argument():
    x = Variable.from_name("x")
    z = Variable.from_name("z")

    identity_x = Abs.named(
        v=x,
        t=x,
    )

    identity_z = Abs.named(
        v=z,
        t=z,
    )

    delayed_argument = App.term(
        identity_z,
        Integer.named(value=7),
    )

    term = App.term(
        identity_x,
        delayed_argument,
    )

    compare_results(
        name="Used delayed argument",
        expression="(λx. x) ((λz. z) 7)",
        term=term,
        expected=7,
    )
