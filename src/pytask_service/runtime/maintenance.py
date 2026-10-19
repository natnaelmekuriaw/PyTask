import sys
from collections.abc import Sequence

from pytask_service.runtime.command import ProcessCommand
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.roles import Role


def migration_command(paths: RuntimePaths) -> ProcessCommand:
    return ProcessCommand(
        Role.MIGRATE,
        (
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(paths.alembic_config),
            "upgrade",
            "head",
        ),
    )


def cli_command(arguments: Sequence[str]) -> ProcessCommand:
    return ProcessCommand(
        Role.CLI,
        (
            sys.executable,
            "-m",
            "pytask_service.cli",
            *(arguments or ["--help"]),
        ),
    )
