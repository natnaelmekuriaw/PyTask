import argparse
from pathlib import Path

from pytask_service.benchmarks.options import BenchmarkOptions, Workload


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="python -m pytask_service.benchmarks",
        description="Measure host Python workers in temporary PostgreSQL schemas.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    command.add_argument(
        "--tasks", type=int, default=20, help="measured tasks per case"
    )
    command.add_argument(
        "--workers",
        type=int,
        nargs="+",
        default=[1, 2, 4],
        help="distinct worker counts; order rotates across repetitions",
    )
    command.add_argument("--repeat", type=int, default=3, help="runs per scenario")
    command.add_argument(
        "--warmup",
        type=int,
        default=2,
        help="unmeasured tasks per case, shared by workers",
    )
    command.add_argument(
        "--workloads",
        nargs="+",
        choices=[workload.value for workload in Workload],
        default=[workload.value for workload in Workload],
        help="registered synthetic workloads",
    )
    command.add_argument(
        "--case-timeout", type=float, default=120, help="seconds per phase"
    )
    command.add_argument(
        "--task-timeout", type=float, default=10, help="handler timeout seconds"
    )
    command.add_argument(
        "--poll-interval", type=float, default=0.05, help="completion poll seconds"
    )
    command.add_argument(
        "--sleep-ms", type=int, default=20, help="sleep workload milliseconds"
    )
    command.add_argument(
        "--iterations", type=int, default=10000, help="SHA-256 rounds per checksum task"
    )
    command.add_argument(
        "--no-recovery",
        action="store_true",
        help="omit the separate crash recovery check",
    )
    command.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-results"),
        help="parent directory for a new report directory per invocation",
    )
    return command


def read_options(args: argparse.Namespace) -> BenchmarkOptions:
    return BenchmarkOptions(
        tasks=args.tasks,
        workers=tuple(args.workers),
        repeat=args.repeat,
        warmup=args.warmup,
        workloads=tuple(Workload(value) for value in args.workloads),
        case_timeout=args.case_timeout,
        task_timeout=args.task_timeout,
        poll_interval=args.poll_interval,
        sleep_ms=args.sleep_ms,
        iterations=args.iterations,
        recovery=not args.no_recovery,
    )
