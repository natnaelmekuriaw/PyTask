import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pytask_service.arguments import InvalidTaskArguments
from pytask_service.config import Settings
from pytask_service.db.engine import build_engine, check_connection
from pytask_service.db.models import TaskStatus
from pytask_service.monitoring import attempt_snapshot, task_snapshot
from pytask_service.policy import TaskPolicy
from pytask_service.registry import UnknownTaskError, load_registry
from pytask_service.tasks import get_task, list_attempts, submit_task
from pytask_service.worker.command import run_forever, run_one
from pytask_service.worker.policy import WorkerPolicy


def main() -> int:
    parser = argparse.ArgumentParser(prog="pytask-service")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-db", help="Check the database connection")
    submit = commands.add_parser("submit", help="Queue a registered task")
    submit.add_argument("name", help="Registered task name")
    input_options = submit.add_mutually_exclusive_group()
    input_options.add_argument(
        "--args", default="{}", help="JSON object of keyword arguments"
    )
    input_options.add_argument(
        "--args-file", type=Path, help="Read arguments from JSON"
    )
    submit.add_argument("--max-attempts", type=int, default=3, help="Total attempts including the first")
    submit.add_argument("--timeout", type=float, default=300, help="Execution deadline in seconds")
    submit.add_argument("--retry-base", type=float, default=1, help="Initial retry backoff in seconds")
    submit.add_argument("--retry-max", type=float, default=60, help="Maximum retry backoff in seconds")
    status = commands.add_parser("status", help="Show a task's current status")
    status.add_argument("id", type=UUID, help="Task ID")
    attempts = commands.add_parser("attempts", help="Show execution attempt history")
    attempts.add_argument("id", type=UUID, help="Task ID")
    worker = commands.add_parser("worker", help="Run queued tasks")
    worker.add_argument("--once", action="store_true", help="Process at most one task")
    worker.add_argument(
        "--poll-interval", type=float, default=0.5, help="Seconds between empty polls"
    )
    worker.add_argument("--lease-seconds", type=float, default=30, help="Lease duration in seconds")
    worker.add_argument("--heartbeat-seconds", type=float, default=10, help="Lease renewal interval")
    args = parser.parse_args()

    if args.command == "check-db":
        try:
            engine = build_engine(Settings.from_env())
            try:
                check_connection(engine)
            finally:
                engine.dispose()
        except (ValueError, SQLAlchemyError) as exc:
            print(f"Database check failed: {exc}", file=sys.stderr)
            return 1
        print("Database connection OK")
        return 0

    if args.command == "submit":
        if args.args_file is not None:
            try:
                raw_arguments = args.args_file.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                print(f"Cannot read argument file: {exc}", file=sys.stderr)
                return 1
        else:
            raw_arguments = args.args
        try:
            policy = TaskPolicy(args.max_attempts, args.timeout, args.retry_base, args.retry_max)
        except ValueError as exc:
            print(f"Task submission failed: {exc}", file=sys.stderr)
            return 1
        return _submit(args.name, raw_arguments, policy)
    if args.command == "status":
        return _inspect_task(args.id, history=False)
    if args.command == "attempts":
        return _inspect_task(args.id, history=True)
    if args.command == "worker":
        try:
            settings = Settings.from_env()
            worker_policy = WorkerPolicy(args.lease_seconds, args.heartbeat_seconds)
            if args.once:
                return run_one(settings, worker_policy)
            return run_forever(settings, args.poll_interval, worker_policy)
        except (ValueError, TypeError, RuntimeError, SQLAlchemyError) as exc:
            print(f"Worker failed: {exc}", file=sys.stderr)
            return 1

    return 2


def _submit(name: str, raw_arguments: str, policy: TaskPolicy | None = None) -> int:
    try:
        settings = Settings.from_env()
        if settings.registry_path is None:
            raise ValueError("PYTASK_REGISTRY is required for submission")
        registry = load_registry(settings.registry_path)
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            raise InvalidTaskArguments("--args must contain valid JSON") from exc

        engine = build_engine(settings)
        try:
            with Session(engine) as session, session.begin():
                task_id = submit_task(session, registry, name, arguments, policy=policy)
        finally:
            engine.dispose()
    except (ValueError, TypeError, UnknownTaskError, SQLAlchemyError) as exc:
        print(f"Task submission failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"id": str(task_id), "status": TaskStatus.PENDING.value}))
    return 0


def _inspect_task(task_id: UUID, *, history: bool) -> int:
    try:
        engine = build_engine(Settings.from_env())
        try:
            with Session(engine) as session:
                task = get_task(session, task_id)
                if task is None:
                    print(f"Task not found: {task_id}", file=sys.stderr)
                    return 1
                details: dict[str, object] | list[dict[str, object]]
                if history:
                    details = [attempt_snapshot(attempt) for attempt in list_attempts(session, task_id)]
                else:
                    details = task_snapshot(task)
        finally:
            engine.dispose()
    except (ValueError, SQLAlchemyError) as exc:
        print(f"Task lookup failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
