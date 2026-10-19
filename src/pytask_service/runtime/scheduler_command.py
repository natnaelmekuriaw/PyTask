import sys

from pytask_service.runtime.command import ProcessCommand
from pytask_service.runtime.roles import Role
from pytask_service.runtime.scheduler_options import SchedulerOptions


def scheduler_command(options: SchedulerOptions) -> ProcessCommand:
    return ProcessCommand(
        Role.SCHEDULER,
        (
            sys.executable,
            "-m",
            "pytask_service.cli",
            "scheduler",
            "--batch-size",
            str(options.batch_size),
            "--poll-interval",
            str(options.poll_seconds),
        ),
    )
