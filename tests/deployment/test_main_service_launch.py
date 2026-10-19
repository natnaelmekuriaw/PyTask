import sys

import pytest

from pytask_service.runtime import main as runtime


@pytest.mark.parametrize("role", ["api", "worker", "scheduler"])
def test_service_launch_follows_preflight_in_order(
    monkeypatch: pytest.MonkeyPatch, role: str
) -> None:
    events: list[str] = []
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@postgres/db")
    monkeypatch.setattr(sys, "argv", ["runtime", role])
    monkeypatch.setattr(
        runtime, "prepare_service", lambda *args: events.append("checked")
    )
    monkeypatch.setattr(
        runtime, "replace_process", lambda command: events.append(command.role.value)
    )
    assert runtime.main() == 0
    assert events == ["checked", role]
