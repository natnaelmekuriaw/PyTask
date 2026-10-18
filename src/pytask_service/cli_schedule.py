import argparse
import json
import sys
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pytask_service.cli_options import add_argument_options, add_policy_options, parse_arguments, read_argument_text, read_policy
from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.registry import UnknownTaskError, load_registry
from pytask_service.scheduling.definitions import create_schedule, get_schedule, list_schedules, set_paused
from pytask_service.scheduling.monitoring import schedule_snapshot
from pytask_service.scheduling.time import parse_timestamp


def configure_schedule_parser(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="schedule_command", required=True)
    create = commands.add_parser("create", help="Create a fixed-interval schedule")
    create.add_argument("name", help="Unique schedule name")
    create.add_argument("task_name", help="Registered task name")
    create.add_argument("--every", type=int, required=True, help="Interval in whole seconds, from 1 to 31536000")
    create.add_argument("--start-at", type=parse_timestamp, help="First due timestamp; defaults to database time")
    add_argument_options(create)
    add_policy_options(create)
    listing = commands.add_parser("list", help="List schedules by name")
    listing.add_argument("--limit", type=int, default=100)
    for action in ("show", "pause", "resume"):
        command = commands.add_parser(action, help=f"{action.capitalize()} a schedule")
        command.add_argument("id", type=UUID)
