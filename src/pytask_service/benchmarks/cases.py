from dataclasses import dataclass

from pytask_service.benchmarks.options import BenchmarkOptions, Workload


@dataclass(frozen=True, slots=True)
class CaseSpec:
    workload: Workload
    workers: int
    repetition: int


def plan_cases(options: BenchmarkOptions) -> tuple[CaseSpec, ...]:
    cases: list[CaseSpec] = []
    for repetition in range(options.repeat):
        offset = repetition % len(options.workers)
        counts = options.workers[offset:] + options.workers[:offset]
        for workload in options.workloads:
            cases.extend(CaseSpec(workload, count, repetition + 1) for count in counts)
    return tuple(cases)
