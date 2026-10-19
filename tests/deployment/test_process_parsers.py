import sys

import pytest
from uvicorn.main import main as uvicorn

from pytask_service import cli
from pytask_service.runtime.api_command import api_command
from pytask_service.runtime.api_options import APIOptions
from pytask_service.runtime.scheduler_command import scheduler_command
from pytask_service.runtime.scheduler_options import SchedulerOptions
from pytask_service.runtime.worker_command import worker_command
from pytask_service.runtime.worker_options import WorkerOptions


def test_api_arguments_parse_without_starting_a_server() -> None:
    command = api_command(APIOptions())
    with uvicorn.make_context("uvicorn", list(command.argv[3:])) as context:
        assert context.params["factory"] is True
        assert context.params["proxy_headers"] is False
        assert context.params["timeout_graceful_shutdown"] == 30


@pytest.mark.parametrize(
    "command",
    [
        worker_command(WorkerOptions()),
        scheduler_command(SchedulerOptions()),
    ],
)
def test_service_arguments_reach_configuration_before_execution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: object,
) -> None:
    def stop() -> None:
        raise ValueError("configuration sentinel")

    monkeypatch.setattr(sys, "argv", ["pytask-service", *command.argv[3:]])
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli.Settings, "from_env", stop)
    assert cli.main() == 1
    assert "configuration sentinel" in capsys.readouterr().err
