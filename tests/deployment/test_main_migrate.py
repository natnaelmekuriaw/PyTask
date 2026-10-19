import sys

import pytest

from pytask_service.runtime import main as runtime


def test_migration_role_launches_only_the_upgrade_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[object] = []

    def unexpected(*args: object) -> None:
        raise AssertionError("migration role must not enter service preflight")

    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@postgres/db")
    monkeypatch.delenv("PYTASK_REGISTRY", raising=False)
    monkeypatch.setattr(sys, "argv", ["runtime", "migrate"])
    monkeypatch.setattr(runtime, "prepare_service", unexpected)
    monkeypatch.setattr(runtime, "replace_process", launched.append)
    assert runtime.main() == 0
    assert len(launched) == 1
    assert launched[0].argv[-2:] == ("upgrade", "head")
