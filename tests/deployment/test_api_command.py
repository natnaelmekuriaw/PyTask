import sys

from pytask_service.runtime.api_command import api_command
from pytask_service.runtime.api_options import APIOptions
from pytask_service.runtime.roles import Role


def test_api_uses_the_current_interpreter_and_explicit_trust_boundary() -> None:
    command = api_command(APIOptions(graceful_seconds=12, concurrency=50))
    assert command.role is Role.API
    assert command.argv[:3] == (sys.executable, "-m", "uvicorn")
    assert command.argv[command.argv.index("--host") + 1] == "0.0.0.0"
    assert command.argv[command.argv.index("--port") + 1] == "8000"
    assert "--no-proxy-headers" in command.argv and "--no-access-log" in command.argv
    assert "--reload" not in command.argv
    assert command.argv[command.argv.index("--timeout-graceful-shutdown") + 1] == "12"
    assert command.argv[command.argv.index("--limit-concurrency") + 1] == "50"
