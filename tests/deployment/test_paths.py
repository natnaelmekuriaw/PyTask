from pathlib import Path

import pytest

from pytask_service.runtime.paths import RuntimePaths


def test_migration_paths_resolve_relative_to_the_working_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "alembic.ini"
    path.write_text("[alembic]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert RuntimePaths.from_env().alembic_config == path


@pytest.mark.parametrize("value", ["", "private-missing-path"])
def test_invalid_paths_have_safe_messages(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("PYTASK_ALEMBIC_CONFIG", value)
    with pytest.raises(ValueError) as failure:
        RuntimePaths.from_env()
    assert str(failure.value) == "PYTASK_ALEMBIC_CONFIG must point to an existing file"
