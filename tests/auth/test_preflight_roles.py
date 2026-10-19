from pathlib import Path

import pytest

from pytask_service.config import Settings
from pytask_service.runtime import preflight
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.roles import Role
from tests.deployment.fakes import Engine


@pytest.mark.parametrize("role", [Role.WORKER, Role.SCHEDULER])
def test_non_http_services_ignore_bad_api_credentials(
    monkeypatch: pytest.MonkeyPatch, role: Role,
) -> None:
    engine = Engine()
    monkeypatch.setenv("PYTASK_API_KEYS", "invalid")
    monkeypatch.setattr(preflight, "build_engine", lambda settings: engine)
    monkeypatch.setattr(preflight, "load_registry", lambda path: None)
    monkeypatch.setattr(preflight, "check_schema", lambda *args: None)
    preflight.prepare_service(
        role, Settings("postgresql+psycopg://u:p@localhost/db", "tasks:registry"),
        RuntimePaths(Path("unused")),
    )
    assert engine.disposed


def test_api_preflight_checks_credentials_before_any_database_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*args: object) -> None:
        raise AssertionError("database accessed before authentication validation")
    monkeypatch.setattr(preflight, "build_engine", unexpected)
    with pytest.raises(ValueError, match="PYTASK_API_KEYS"):
        preflight.prepare_service(
            Role.API, Settings("postgresql+psycopg://u:p@localhost/db", "tasks:registry"),
            RuntimePaths(Path("unused")),
        )

