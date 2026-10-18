import argparse
import json
from pathlib import Path

from pytask_service.arguments import InvalidTaskArguments
from pytask_service.policy import TaskPolicy


def add_argument_options(parser: argparse.ArgumentParser) -> None:
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--args", default="{}", help="JSON object of keyword arguments")
    options.add_argument("--args-file", type=Path, help="Read arguments from JSON")


def add_policy_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-attempts", type=int, default=3, help="Total attempts including the first")
    parser.add_argument("--timeout", type=float, default=300, help="Execution deadline in seconds")
    parser.add_argument("--retry-base", type=float, default=1, help="Initial retry backoff in seconds")
    parser.add_argument("--retry-max", type=float, default=60, help="Maximum retry backoff in seconds")


def read_argument_text(args: argparse.Namespace) -> str:
    path: Path | None = args.args_file
    raw: str = args.args
    return path.read_text(encoding="utf-8") if path is not None else raw


def parse_arguments(raw: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise InvalidTaskArguments("--args must contain valid JSON") from error


def read_policy(args: argparse.Namespace) -> TaskPolicy:
    return TaskPolicy(args.max_attempts, args.timeout, args.retry_base, args.retry_max)
