from pathlib import Path

import pytest

from pytask_service.runtime import schema
from pytask_service.runtime.paths import RuntimePaths


def test_packaged_project_scripts_have_a_single_head() -> None:
    root = Path(__file__).resolve().parents[2]
    assert schema.expected_heads(RuntimePaths(root / "alembic.ini")) == frozenset(
        {"20261019_07"}
    )


def test_empty_migration_histories_are_not_treated_as_current(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Scripts:
        def get_heads(self) -> list[str]:
            return []

    monkeypatch.setattr(schema.ScriptDirectory, "from_config", lambda config: Scripts())
    with pytest.raises(schema.RuntimeFailure, match="no migration heads"):
        schema.expected_heads(RuntimePaths(Path("unused")))
