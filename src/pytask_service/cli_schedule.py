import argparse
import json
import sys
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from pytask_service.cli_options import (
    add_argument_options,
    add_policy_options,
    parse_arguments,
    read_argument_text,
    read_policy,
)
from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.monitoring import task_snapshot
from pytask_service.registry import UnknownTaskError, load_registry
from pytask_service.scheduling.definitions import (
    create_schedule,
    get_schedule,
    list_occurrences,
    list_schedules,
    set_paused,
)
from pytask_service.scheduling.monitoring import schedule_snapshot
from pytask_service.scheduling.time import parse_timestamp


def configure_schedule_parser(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="schedule_command", required=True)
    create = commands.add_parser("create", help="Create a fixed-interval schedule")
    create.add_argument("name", help="Unique schedule name")
    create.add_argument("task_name", help="Registered task name")
    create.add_argument(
        "--every",
        type=int,
        required=True,
        help="Interval in whole seconds, from 1 to 31536000",
    )
    create.add_argument(
        "--start-at",
        type=parse_timestamp,
        help="First due timestamp; defaults to database time",
    )
    add_argument_options(create)
    add_policy_options(create)
    create.add_argument(
        "--paused", action="store_true", help="Create without dispatching until resumed"
    )
    listing = commands.add_parser("list", help="List schedules by name")
    listing.add_argument("--limit", type=int, default=100)
    for action in ("show", "pause", "resume"):
        command = commands.add_parser(action, help=f"{action.capitalize()} a schedule")
        command.add_argument("id", type=UUID)
    history = commands.add_parser("history", help="Show recent task occurrences")
    history.add_argument("id", type=UUID)
    history.add_argument("--limit", type=int, default=100)


def handle_schedule(args: argparse.Namespace) -> int:
    try:
        settings = Settings.from_env()
        registry = None
        arguments: object = None
        policy = None
        if args.schedule_command == "create":
            if settings.registry_path is None:
                raise ValueError("PYTASK_REGISTRY is required for schedule creation")
            registry = load_registry(settings.registry_path)
            arguments = parse_arguments(read_argument_text(args))
            policy = read_policy(args)
        engine = build_engine(settings)
        try:
            with Session(engine) as session, session.begin():
                if args.schedule_command == "create":
                    assert registry is not None
                    schedule = create_schedule(
                        session,
                        registry,
                        args.name,
                        args.task_name,
                        arguments,
                        interval_seconds=args.every,
                        start_at=args.start_at,
                        policy=policy,
                        paused=args.paused,
                    )
                    details: object = schedule_snapshot(schedule)
                elif args.schedule_command == "list":
                    details = [
                        schedule_snapshot(item)
                        for item in list_schedules(session, limit=args.limit)
                    ]
                elif args.schedule_command in ("pause", "resume"):
                    details = schedule_snapshot(
                        set_paused(session, args.id, args.schedule_command == "pause")
                    )
                else:
                    found_schedule = get_schedule(session, args.id)
                    if found_schedule is None:
                        raise ValueError(f"Schedule not found: {args.id}")
                    details = (
                        [
                            task_snapshot(task)
                            for task in list_occurrences(
                                session, args.id, limit=args.limit
                            )
                        ]
                        if args.schedule_command == "history"
                        else schedule_snapshot(found_schedule)
                    )
        finally:
            engine.dispose()
    except IntegrityError as error:
        constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_schedules_name":
            print("Schedule name already exists", file=sys.stderr)
        else:
            print(f"Schedule command failed: {error}", file=sys.stderr)
        return 1
    except (
        ValueError,
        TypeError,
        OSError,
        UnicodeError,
        UnknownTaskError,
        SQLAlchemyError,
    ) as error:
        print(f"Schedule command failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(details))
    return 0
