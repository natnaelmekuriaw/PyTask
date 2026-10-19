import csv
from io import StringIO

from pytask_service.benchmarks.report import BenchmarkReport

COLUMNS = (
    "workload", "workers", "repetition", "valid", "error_code", "submitted",
    "succeeded", "attempts", "elapsed_seconds", "submission_seconds",
    "throughput_per_second", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms",
    "queue_wait_p95_ms", "attempt_p95_ms",
)


def render_csv(report: BenchmarkReport) -> str:
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLUMNS)
    writer.writeheader()
    for result in report.results:
        row: dict[str, object] = {
            "workload": result.case.workload.value, "workers": result.case.workers,
            "repetition": result.case.repetition, "valid": result.valid,
            "error_code": result.error_code or "",
        }
        metrics = result.metrics if result.valid else None
        if metrics:
            row.update({
                "submitted": metrics.submitted, "succeeded": metrics.succeeded,
                "attempts": metrics.attempts, "elapsed_seconds": metrics.elapsed_seconds,
                "submission_seconds": metrics.submission_seconds,
                "throughput_per_second": metrics.throughput_per_second,
            })
            for name, value in (
                ("latency_p50_ms", metrics.latency_seconds.p50),
                ("latency_p95_ms", metrics.latency_seconds.p95),
                ("latency_p99_ms", metrics.latency_seconds.p99),
                ("queue_wait_p95_ms", metrics.queue_wait_seconds.p95),
                ("attempt_p95_ms", metrics.attempt_seconds.p95),
            ):
                row[name] = value * 1000 if value is not None else ""
        writer.writerow(row)
    return stream.getvalue()

