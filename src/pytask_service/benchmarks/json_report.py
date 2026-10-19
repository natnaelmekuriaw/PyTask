import json

from pytask_service.benchmarks.report import BenchmarkReport


def render_json(report: BenchmarkReport) -> str:
    return (
        json.dumps(report.document(), indent=2, allow_nan=False, ensure_ascii=True)
        + "\n"
    )
