import pytest

from pytask_service.benchmarks.options import BenchmarkOptions


@pytest.mark.parametrize(
    "name,value",
    [
        ("tasks", 0),
        ("tasks", True),
        ("repeat", 11),
        ("warmup", -1),
        ("sleep_ms", 1001),
        ("iterations", 0),
        ("iterations", 1000001),
    ],
)
def test_invalid_integer_settings(name, value):
    with pytest.raises(ValueError):
        BenchmarkOptions(**{name: value})


def test_total_task_budget_includes_warmup_and_repetitions():
    with pytest.raises(ValueError, match="100000"):
        BenchmarkOptions(tasks=10000, workers=(1, 2, 4, 8), repeat=10)


def test_upper_task_count_is_accepted_for_a_small_plan():
    assert BenchmarkOptions(tasks=10000, workers=(1,), repeat=1).tasks == 10000
