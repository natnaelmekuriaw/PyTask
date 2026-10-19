from dataclasses import dataclass
from statistics import median

from pytask_service.benchmarks.options import Workload
from pytask_service.benchmarks.results import CaseResult


@dataclass(frozen=True, slots=True)
class ScenarioSummary:
    workload: Workload
    workers: int
    repetitions: int
    valid_repetitions: int
    median_throughput: float | None
    minimum_throughput: float | None
    maximum_throughput: float | None
    speedup: float | None


def summarize(
    results: tuple[CaseResult, ...], expected_repetitions: int
) -> tuple[ScenarioSummary, ...]:
    groups: dict[tuple[Workload, int], list[CaseResult]] = {}
    for result in results:
        groups.setdefault((result.case.workload, result.case.workers), []).append(result)
    baselines: dict[Workload, float] = {}
    for (workload, workers), rows in groups.items():
        values = [row.metrics.throughput_per_second for row in rows if row.valid and row.metrics]
        repetitions = {row.case.repetition for row in rows}
        complete = (
            len(values) == len(rows) == expected_repetitions
            and repetitions == set(range(1, expected_repetitions + 1))
        )
        if workers == 1 and values and complete:
            baselines[workload] = median(values)
    summaries = []
    for (workload, workers), rows in groups.items():
        values = [row.metrics.throughput_per_second for row in rows if row.valid and row.metrics]
        complete = (
            bool(values) and len(values) == len(rows) == expected_repetitions
            and {row.case.repetition for row in rows} == set(range(1, expected_repetitions + 1))
        )
        central = median(values) if complete else None
        baseline = baselines.get(workload)
        summaries.append(ScenarioSummary(
            workload, workers, len(rows), len(values), central,
            min(values) if complete else None, max(values) if complete else None,
            central / baseline if central is not None and baseline else None,
        ))
    return tuple(summaries)

