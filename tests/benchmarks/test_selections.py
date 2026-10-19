import pytest

from pytask_service.benchmarks.options import BenchmarkOptions, Workload


@pytest.mark.parametrize(
    "workers", [(), (1, 1), (0,), (33,), (True,), [1], tuple(range(1, 10))]
)
def test_invalid_worker_selection(workers):
    with pytest.raises(ValueError, match="workers"):
        BenchmarkOptions(workers=workers)


@pytest.mark.parametrize(
    "workloads", [(), ("noop",), [Workload.NOOP], (Workload.NOOP,) * 2]
)
def test_workloads_are_distinct_immutable_enum_values(workloads):
    with pytest.raises(ValueError, match="workloads"):
        BenchmarkOptions(workloads=workloads)


def test_custom_order_is_preserved():
    options = BenchmarkOptions(
        workers=(4, 1), workloads=(Workload.SLEEP, Workload.NOOP)
    )
    assert options.workers == (4, 1)
    assert options.workloads == (Workload.SLEEP, Workload.NOOP)
