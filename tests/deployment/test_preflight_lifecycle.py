from pathlib import Path

import pytest

from pytask_service.config import Settings
from pytask_service.runtime import preflight
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.roles import Role
from pytask_service.runtime.schema import RuntimeFailure
from tests.deployment.fakes import Engine


@pytest.mark.parametrize("fails", [False, True])
def test_scheduler_preflight_needs_no_registry_and_always_disposes(
    monkeypatch: pytest.MonkeyPatch,
    fails: bool,
) -> None:
    engine = Engine()

    def check(database: object, paths: object) -> None:
        assert database is engine
        if fails:
            raise RuntimeFailure("schema mismatch")

    monkeypatch.setattr(preflight, "build_engine", lambda settings: engine)
    monkeypatch.setattr(preflight, "check_schema", check)
    settings = Settings("postgresql+psycopg://u:p@postgres/db")
    if fails:
        with pytest.raises(RuntimeFailure, match="schema mismatch"):
            preflight.prepare_service(
                Role.SCHEDULER, settings, RuntimePaths(Path("unused"))
            )
    else:
        preflight.prepare_service(
            Role.SCHEDULER, settings, RuntimePaths(Path("unused"))
        )
    assert engine.disposed
