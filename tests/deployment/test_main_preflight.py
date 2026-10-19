import sys

import pytest

from pytask_service.runtime import main as runtime
from pytask_service.runtime.schema import RuntimeFailure


@pytest.mark.parametrize("role", ["api", "worker", "scheduler"])
def test_failed_preflight_never_replaces_the_process(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    role: str,
) -> None:
    launched: list[object] = []

    def fail(*args: object) -> None:
        raise RuntimeFailure("schema mismatch")

    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@postgres/db")
    monkeypatch.setattr(sys, "argv", ["runtime", role])
    monkeypatch.setattr(runtime, "prepare_service", fail)
    monkeypatch.setattr(runtime, "replace_process", launched.append)
    assert runtime.main() == 1
    assert not launched
    assert capsys.readouterr().err == "Runtime check failed: schema mismatch\n"
