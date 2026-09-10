import statistics
import time

from pgsn.pgsn_term import Abs, App, Integer, Variable
from pgsn_env_eval import (
    eval_env,
    set_metrics_enabled,
)


def identity():
    x = Variable.from_name("x")
    return App.term(
        Abs.named(v=x, t=x),
        Integer.named(value=5),
    )


def constant_function():
    x = Variable.from_name("x")
    return App.term(
        Abs.named(v=x, t=Integer.named(value=1)),
        Integer.named(value=5),
    )


def captured_variable():
    x = Variable.from_name("x")
    y = Variable.from_name("y")

    term = Abs.named(
        v=x,
        t=Abs.named(v=y, t=x),
    )

    term = App.term(term, Integer.named(value=5))
    term = App.term(term, Integer.named(value=10))
    return term


def function_argument():
    f = Variable.from_name("f")
    x = Variable.from_name("x")

    identity_fn = Abs.named(v=x, t=x)

    apply_f = Abs.named(
        v=f,
        t=App.term(f, Integer.named(value=5)),
    )

    return App.term(apply_f, identity_fn)


def unused_argument():
    x = Variable.from_name("x")

    invalid_argument = App.term(
        Integer.named(value=1),
        Integer.named(value=2),
    )

    return App.term(
        Abs.named(v=x, t=Integer.named(value=1)),
        invalid_argument,
    )


def used_delayed_argument():
    x = Variable.from_name("x")
    z = Variable.from_name("z")

    delayed = App.term(
        Abs.named(v=z, t=z),
        Integer.named(value=7),
    )

    return App.term(
        Abs.named(v=x, t=x),
        delayed,
    )


def deep_captured_variable(depth=100):
    x = Variable.from_name("x")
    body = x

    for i in reversed(range(depth)):
        y = Variable.from_name(f"y{i}")
        body = Abs.named(v=y, t=body)

    term = App.term(
        Abs.named(v=x, t=body),
        Integer.named(value=5),
    )

    for _ in range(depth):
        term = App.term(
            term,
            Integer.named(value=0),
        )

    return term


def measure(func, runs, batches=7):
    times = []

    for _ in range(batches):
        start = time.perf_counter()

        for _ in range(runs):
            func()

        elapsed = time.perf_counter() - start
        times.append(elapsed / runs)

    return statistics.median(times)


def benchmark(name, term, runs):
    # Check correctness once before timing.
    current_result = term.fully_eval()
    env_result = eval_env(term)

    assert current_result.value == env_result.value

    # Warm-up
    for _ in range(5):
        term.fully_eval()
        eval_env(term)

    current_time = measure(term.fully_eval, runs)
    env_time = measure(lambda: eval_env(term), runs)

    ratio = current_time / env_time

    print(f"\n=== {name} ===")
    print(f"Runs per batch: {runs}")
    print(f"Current evaluator:     {current_time * 1000:.6f} ms")
    print(f"Environment evaluator: {env_time * 1000:.6f} ms")
    print(f"Current / Environment: {ratio:.2f}x")


def main():
    set_metrics_enabled(False)

    small_tests = [
        ("Identity", identity(), 1000),
        ("Constant function", constant_function(), 1000),
        ("Captured variable", captured_variable(), 1000),
        ("Function argument", function_argument(), 1000),
        ("Unused argument", unused_argument(), 1000),
        ("Used delayed argument", used_delayed_argument(), 1000),
    ]

    print("\n=== Small comparison benchmarks ===")

    for name, term, runs in small_tests:
        benchmark(name, term, runs)

    print("\n=== Deep captured-variable scaling ===")

    for depth in [10, 25, 50, 100, 200]:
        benchmark(
            f"Deep captured variable (depth={depth})",
            deep_captured_variable(depth),
            100,
        )


if __name__ == "__main__":
    main()
