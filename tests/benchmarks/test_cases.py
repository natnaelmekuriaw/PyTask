from pytask_service.benchmarks.cases import plan_cases
from pytask_service.benchmarks.options import BenchmarkOptions, Workload


def test_each_repetition_rotates_worker_order():
    options = BenchmarkOptions(workloads=(Workload.NOOP,))
    cases = plan_cases(options)
    assert [case.workers for case in cases] == [1, 2, 4, 2, 4, 1, 4, 1, 2]
    assert [case.repetition for case in cases] == [1] * 3 + [2] * 3 + [3] * 3


def test_default_plan_covers_every_scenario_once_per_repeat():
    cases = plan_cases(BenchmarkOptions())
    assert len(cases) == 27
    assert len(set(cases)) == 27
    for workload in Workload:
        for workers in (1, 2, 4):
            assert {
                case.repetition
                for case in cases
                if case.workload == workload and case.workers == workers
            } == {1, 2, 3}
