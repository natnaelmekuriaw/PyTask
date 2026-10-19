from dataclasses import dataclass

from pytask_service.benchmarks.options import BenchmarkOptions, Workload
from pytask_service.benchmarks.workloads import checksum


@dataclass(frozen=True, slots=True)
class WorkItem:
    name: str
    arguments: dict[str, object]
    expected: object


def work_item(workload: Workload, index: int, options: BenchmarkOptions) -> WorkItem:
    if workload is Workload.NOOP:
        return WorkItem("benchmark.noop", {"index": index}, index)
    if workload is Workload.SLEEP:
        return WorkItem("benchmark.sleep", {"index": index, "milliseconds": options.sleep_ms}, index)
    if workload is Workload.CHECKSUM:
        return WorkItem(
            "benchmark.checksum", {"index": index, "iterations": options.iterations},
            checksum(index, options.iterations),
        )
    raise ValueError("Unsupported benchmark workload")

