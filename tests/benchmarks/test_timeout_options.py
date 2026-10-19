import pytest

from pytask_service.benchmarks.options import BenchmarkOptions


@pytest.mark.parametrize("value", [True, "10", float("nan"), float("inf"), -1, 0])
@pytest.mark.parametrize("field", ["case_timeout", "task_timeout", "poll_interval"])
def test_time_settings_require_finite_numbers(field, value):
    with pytest.raises(ValueError):
        BenchmarkOptions(**{field: value})


@pytest.mark.parametrize("value", [0, 1, None, "false"])
def test_recovery_switch_requires_a_boolean(value):
    with pytest.raises(ValueError, match="boolean"):
        BenchmarkOptions(recovery=value)


def test_time_boundaries_are_inclusive():
    options = BenchmarkOptions(case_timeout=5, task_timeout=120, poll_interval=0.01)
    assert options.case_timeout == 5
