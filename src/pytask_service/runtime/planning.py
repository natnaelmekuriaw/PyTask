from collections.abc import Sequence

from pytask_service.runtime.api_command import api_command
from pytask_service.runtime.api_options import APIOptions
from pytask_service.runtime.command import ProcessCommand
from pytask_service.runtime.maintenance import cli_command, migration_command
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.roles import Role
from pytask_service.runtime.scheduler_command import scheduler_command
from pytask_service.runtime.scheduler_options import SchedulerOptions
from pytask_service.runtime.worker_command import worker_command
from pytask_service.runtime.worker_options import WorkerOptions


def plan_command(role: Role, arguments: Sequence[str]) -> ProcessCommand:
    if role == Role.CLI:
        return cli_command(arguments)
    if arguments:
        raise ValueError(
            "Service roles do not accept extra arguments; use the cli role"
        )
    if role == Role.API:
        return api_command(APIOptions.from_env())
    if role == Role.WORKER:
        return worker_command(WorkerOptions.from_env())
    if role == Role.SCHEDULER:
        return scheduler_command(SchedulerOptions.from_env())
    if role == Role.MIGRATE:
        return migration_command(RuntimePaths.from_env())
    raise ValueError("This role does not launch a process")
