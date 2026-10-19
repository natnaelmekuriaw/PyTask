import argparse
from pathlib import Path

from pytask_service.benchmarks.options import BenchmarkOptions, Workload


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="python -m pytask_service.benchmarks")
    command.add_argument("--tasks", type=int, default=20)
    command.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4])
    command.add_argument("--repeat", type=int, default=3)
    command.add_argument("--warmup", type=int, default=2)
    command.add_argument("--workloads", nargs="+", choices=list(Workload), default=list(Workload))
    command.add_argument("--case-timeout", type=float, default=120)
    command.add_argument("--task-timeout", type=float, default=10)
    command.add_argument("--poll-interval", type=float, default=0.05)
    command.add_argument("--sleep-ms", type=int, default=20)
    command.add_argument("--iterations", type=int, default=10000)
    command.add_argument("--no-recovery", action="store_true")
    command.add_argument("--output", type=Path, default=Path("benchmark-results"))
    return command


def read_options(args: argparse.Namespace) -> BenchmarkOptions:
    return BenchmarkOptions(
        tasks=args.tasks, workers=tuple(args.workers), repeat=args.repeat,
        warmup=args.warmup, workloads=tuple(Workload(value) for value in args.workloads),
        case_timeout=args.case_timeout, task_timeout=args.task_timeout,
        poll_interval=args.poll_interval, sleep_ms=args.sleep_ms,
        iterations=args.iterations, recovery=not args.no_recovery,
    )

