import argparse
import sys

from sqlalchemy.exc import SQLAlchemyError

from pytask_service.config import Settings
from pytask_service.db.diagnostics import postgres_state
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.planning import plan_command
from pytask_service.runtime.preflight import prepare_service
from pytask_service.runtime.probe import run_probe
from pytask_service.runtime.process import replace_process
from pytask_service.runtime.roles import Role
from pytask_service.runtime.schema import RuntimeFailure


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m pytask_service.runtime")
    parser.add_argument("role", choices=[role.value for role in Role])
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    role = Role(args.role)
    try:
        if role == Role.PROBE:
            if len(args.arguments) != 1:
                raise ValueError("probe requires exactly one kind: api or database")
            return run_probe(args.arguments[0])
        if role == Role.CHECK:
            if args.arguments:
                raise ValueError("check does not accept arguments")
            return run_probe("database")
        command = plan_command(role, args.arguments)
        if role in {Role.API, Role.WORKER, Role.SCHEDULER}:
            prepare_service(role, Settings.from_env(), RuntimePaths.from_env())
        elif role == Role.MIGRATE:
            Settings.from_env()
        replace_process(command)
    except ValueError as error:
        print(f"Runtime configuration failed: {error}", file=sys.stderr)
        return 1
    except RuntimeFailure as error:
        print(f"Runtime check failed: {error}", file=sys.stderr)
        return 1
    except SQLAlchemyError as error:
        state = postgres_state(error)
        suffix = f" (SQLSTATE {state})" if state is not None else ""
        print(
            f"Database preflight failed{suffix}; "
            "check connection, permissions, and migrations",
            file=sys.stderr,
        )
        return 1
    except OSError:
        print(
            "Cannot start runtime process; check the image installation",
            file=sys.stderr,
        )
        return 1
    return 0
