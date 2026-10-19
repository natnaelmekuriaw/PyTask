import sys
from pathlib import Path

from pytask_service.runtime.maintenance import cli_command, migration_command
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.roles import Role


def test_migrations_use_an_explicit_config_and_upgrade_target() -> None:
    path = Path("path with spaces/alembic.ini")
    command = migration_command(RuntimePaths(path))
    assert command.role is Role.MIGRATE
    assert command.argv == (
        sys.executable,
        "-m",
        "alembic",
        "-c",
        str(path),
        "upgrade",
        "head",
    )


def test_operator_arguments_keep_metacharacters_literal() -> None:
    arguments = ["submit", "task.name", "--args", '{"value":"$HOME; $(command)"}']
    command = cli_command(arguments)
    assert command.argv[:3] == (sys.executable, "-m", "pytask_service.cli")
    assert list(command.argv[3:]) == arguments
    assert cli_command([]).argv[-1] == "--help"
