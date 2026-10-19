import sys

from pytask_service.runtime.api_options import APIOptions
from pytask_service.runtime.command import ProcessCommand
from pytask_service.runtime.roles import Role


def api_command(options: APIOptions) -> ProcessCommand:
    return ProcessCommand(
        Role.API,
        (
            sys.executable,
            "-m",
            "uvicorn",
            "pytask_service.api.app:create_app",
            "--factory",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--no-proxy-headers",
            "--no-access-log",
            "--log-level",
            "warning",
            "--timeout-graceful-shutdown",
            str(options.graceful_seconds),
            "--limit-concurrency",
            str(options.concurrency),
            "--timeout-keep-alive",
            str(options.keep_alive_seconds),
        ),
    )
