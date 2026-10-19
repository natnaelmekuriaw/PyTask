import sys

import pytest

from pytask_service.runtime import process
from pytask_service.runtime.command import ProcessCommand
from pytask_service.runtime.roles import Role


def test_launch_replaces_the_process_without_shell_interpretation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        process.os,
        "execv",
        lambda executable, arguments: calls.append((executable, arguments)),
    )
    command = ProcessCommand(
        Role.CLI, (sys.executable, "-m", "pytask_service.cli", "stats")
    )
    process.replace_process(command)
    assert calls == [(sys.executable, command.argv)]
