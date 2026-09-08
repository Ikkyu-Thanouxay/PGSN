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
