import sys

import pytest

from pytask_service.runtime import main as runtime


def test_cli_help_can_launch_without_database_or_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[object] = []
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.delenv("PYTASK_REGISTRY", raising=False)
    monkeypatch.setenv("PYTASK_ALEMBIC_CONFIG", "missing")
    monkeypatch.setattr(sys, "argv", ["runtime", "cli"])
    monkeypatch.setattr(runtime, "replace_process", launched.append)
    assert runtime.main() == 0
    assert len(launched) == 1 and launched[0].argv[-1] == "--help"


def test_top_level_help_does_not_load_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["runtime", "--help"])
    with pytest.raises(SystemExit) as result:
        runtime.main()
    assert result.value.code == 0
