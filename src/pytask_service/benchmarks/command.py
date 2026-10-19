import json
import sys
from collections.abc import Sequence

from pytask_service.benchmarks.arguments import parser, read_options
from pytask_service.benchmarks.artifacts import write_reports
from pytask_service.benchmarks.suite import run_suite
from pytask_service.config import Settings


def main(argv: Sequence[str] | None = None) -> int:
    command = parser()
    args = command.parse_args(argv)
    try:
        options = read_options(args)
        settings = Settings.from_env()
    except ValueError as error:
        print(f"Benchmark configuration failed: {error}", file=sys.stderr)
        return 2
    report = run_suite(settings, options, progress=lambda message: print(message, file=sys.stderr, flush=True))
    try:
        output = write_reports(report, args.output)
    except (OSError, ValueError):
        print("Cannot save benchmark reports; check output directory access.", file=sys.stderr)
        return 1
    print(json.dumps({
        "valid": report.valid, "completed_cases": len(report.results),
        "report_directory": str(output), "error_code": report.error_code,
    }))
    if report.error_code == "interrupted":
        return 130
    return 0 if report.valid else 1

