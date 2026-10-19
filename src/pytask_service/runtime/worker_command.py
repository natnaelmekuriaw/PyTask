import sys

from pytask_service.runtime.command import ProcessCommand
from pytask_service.runtime.roles import Role
from pytask_service.runtime.worker_options import WorkerOptions


def worker_command(options: WorkerOptions) -> ProcessCommand:
    return ProcessCommand(
        Role.WORKER,
        (
            sys.executable,
            "-m",
            "pytask_service.cli",
            "worker",
            "--poll-interval",
            str(options.poll_seconds),
            "--lease-seconds",
            str(options.lease_seconds),
            "--heartbeat-seconds",
            str(options.heartbeat_seconds),
        ),
    )
