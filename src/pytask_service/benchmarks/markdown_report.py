from pytask_service.benchmarks.report import BenchmarkReport
from pytask_service.benchmarks.summary import summarize


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _number(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


def render_markdown(report: BenchmarkReport) -> str:
    environment = report.environment
    lines = [
        "# PyTask benchmark results", "",
        f"Complete valid run: **{report.valid}**", "",
        f"- Python: {_cell(environment.python)} ({_cell(environment.implementation)})",
        f"- Platform: {_cell(environment.platform)}",
        f"- Logical CPUs: {_cell(environment.logical_cpus)}",
        f"- PostgreSQL: {_cell(environment.postgres)}",
        f"- Revision: {_cell(environment.revision)}; tracked changes: {environment.tracked_changes}",
        "", "## Throughput across repetitions", "",
        "| Workload | Workers | Valid / observed runs | Median tasks/s | Min | Max | Speedup |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summarize(report.results):
        lines.append(
            f"| {row.workload.value} | {row.workers} | {row.valid_repetitions}/{row.repetitions} "
            f"| {_number(row.median_throughput)} | {_number(row.minimum_throughput)} "
            f"| {_number(row.maximum_throughput)} | {_number(row.speedup)} |"
        )
    lines += [
        "", "## Individual runs", "",
        "| Workload | Workers | Repeat | Valid | Tasks/s | Latency p95 ms | Error |",
        "| --- | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in report.results:
        metrics = row.metrics if row.valid else None
        throughput = metrics.throughput_per_second if metrics else None
        latency = metrics.latency_seconds.p95 if metrics else None
        lines.append(
            f"| {row.case.workload.value} | {row.case.workers} | {row.case.repetition} "
            f"| {row.valid} | {_number(throughput)} | {_number(latency * 1000 if latency is not None else None)} "
            f"| {_cell(row.error_code or '')} |"
        )
        if row.retained_schema:
            lines += ["", f"Retained schema: `{_cell(row.retained_schema)}`", ""]
    lines += ["", "## Recovery check", ""]
    if report.recovery is not None:
        recovery = report.recovery
        lines += [
            f"Valid: {recovery.valid}; elapsed seconds: {_number(recovery.elapsed_seconds)}.",
            f"Attempt outcomes: {', '.join(recovery.attempt_statuses) or 'unavailable'}.",
            f"Error: {_cell(recovery.error_code or 'none')}.",
        ]
        if recovery.retained_schema:
            lines += [f"Retained schema: `{_cell(recovery.retained_schema)}`."]
    else:
        lines += ["Not executed."]
    lines += [
        "", "## Interpretation", "",
        "These are host Python engine measurements against the configured PostgreSQL server.",
        "Warmup and worker startup are excluded. Submission and observation overhead are included.",
        "Attempt timing includes handler process startup and cleanup, not just handler CPU time.",
        "Invalid or incomplete repetition groups have no throughput summary or speedup.",
        "Recovery covers a worker lost before handler execution; handlers still need idempotency.",
        "Keep the JSON report with this table when publishing results.", "",
    ]
    return "\n".join(lines)

