from pgsn.pgsn_term import (
    Abs,
    App,
    Integer,
    Variable,
    start_evaluation_metrics,
    stop_evaluation_metrics,
)
from pgsn.dsl import plus, minus, times, div, integer

from pgsn_env_eval import (
    eval_env,
    reset_environment_lookup_count,
    get_environment_lookup_count,
    reset_closure_creation_count,
    get_closure_creation_count,
    reset_delayed_argument_creation_count,
    get_delayed_argument_creation_count,
    reset_delayed_argument_evaluation_count,
    get_delayed_argument_evaluation_count,
)


def compare_results(name, expression, term, expected):
    start_evaluation_metrics()
    current_result = term.fully_eval()
    current_metrics = stop_evaluation_metrics()

    reset_environment_lookup_count()
    reset_closure_creation_count()
    reset_delayed_argument_creation_count()
    reset_delayed_argument_evaluation_count()

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

    print("Current evaluator metrics:")
    print(f"  beta reductions:     {current_metrics.beta_reductions}")
    print(f"  shift node visits:   {current_metrics.shift_node_visits}")
    print(f"  subst node visits:   {current_metrics.subst_node_visits}")

    print("Environment evaluator metrics:")
    print(f"  environment lookups: {get_environment_lookup_count()}")
    print(f"  closures created:    {get_closure_creation_count()}")
    print(f"  delayed created:     {get_delayed_argument_creation_count()}")
    print(f"  delayed evaluated:   {get_delayed_argument_evaluation_count()}")

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


def test_deep_captured_variable():
    depth = 100

    x = Variable.from_name("x")
    body = x

    # λy0. λy1. ... λy99. x
    for i in reversed(range(depth)):
        y = Variable.from_name(f"y{i}")
        body = Abs.named(
            v=y,
            t=body,
        )

    # (λx. λy0. ... λy99. x) 5
    term = App.term(
        Abs.named(v=x, t=body),
        Integer.named(value=5),
    )

    # Apply all 100 inner lambdas to 0. -> (λx. λy0. ... λy99. x) 5 0 0 ... 0
    for _ in range(depth):
        term = App.term(
            term,
            Integer.named(value=0),
        )

    compare_results(
        name="Deep captured variable",
        expression="100 nested lambdas capturing x",
        term=term,
        expected=5,
    )



def test_plus_builtin():
    term = plus(integer(7), integer(3))

    compare_results(
        name="Builtin plus",
        expression="plus 7 3",
        term=term,
        expected=10,
    )


def test_minus_builtin():
    term = minus(integer(7), integer(3))

    compare_results(
        name="Builtin minus",
        expression="minus 7 3",
        term=term,
        expected=4,
    )


def test_times_builtin():
    term = times(integer(7), integer(3))

    compare_results(
        name="Builtin times",
        expression="times 7 3",
        term=term,
        expected=21,
    )


def test_div_builtin():
    term = div(integer(7), integer(3))

    compare_results(
        name="Builtin div",
        expression="div 7 3",
        term=term,
        expected=2,
    )


def test_builtin_argument_from_environment():
    x = Variable.from_name("x")

    body = App.term(
        App.term(plus, x),
        integer(3),
    )

    term = App.term(
        Abs.named(v=x, t=body),
        integer(7),
    )

    compare_results(
        name="Builtin argument from environment",
        expression="(lambda x. plus x 3) 7",
        term=term,
        expected=10,
    )


def test_builtin_passed_as_function():
    f = Variable.from_name("f")

    body = App.term(
        App.term(f, integer(7)),
        integer(3),
    )

    term = App.term(
        Abs.named(v=f, t=body),
        plus,
    )

    compare_results(
        name="Builtin passed as function",
        expression="(lambda f. f 7 3) plus",
        term=term,
        expected=10,
    )
