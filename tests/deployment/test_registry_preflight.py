from pathlib import Path

import pytest

from pytask_service.config import Settings
from pytask_service.runtime import preflight
from pytask_service.runtime.paths import RuntimePaths
from pytask_service.runtime.roles import Role


@pytest.mark.parametrize("role", [Role.API, Role.WORKER])
def test_missing_registry_does_not_open_connections(
    monkeypatch: pytest.MonkeyPatch, role: Role
) -> None:
    def unexpected(settings: object) -> None:
        raise AssertionError("database access before registry validation")

    monkeypatch.setattr(preflight, "build_engine", unexpected)
    with pytest.raises(ValueError, match="PYTASK_REGISTRY"):
        preflight.prepare_service(
            role,
            Settings("postgresql+psycopg://u:p@postgres/db"),
            RuntimePaths(Path("unused")),
        )


def test_wrong_registry_type_has_a_safe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def invalid(path: str) -> None:
        raise TypeError("private implementation details")

    monkeypatch.setattr(preflight, "load_registry", invalid)
    settings = Settings("postgresql+psycopg://u:p@postgres/db", "tasks:registry")
    with pytest.raises(ValueError) as failure:
        preflight.prepare_service(Role.API, settings, RuntimePaths(Path("unused")))
    assert str(failure.value) == "PYTASK_REGISTRY must refer to a TaskRegistry"
