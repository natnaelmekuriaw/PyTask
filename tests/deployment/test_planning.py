import pytest

from pytask_service.runtime.planning import plan_command
from pytask_service.runtime.roles import Role


@pytest.mark.parametrize("role", [Role.API, Role.WORKER, Role.SCHEDULER, Role.MIGRATE])
def test_service_extra_arguments_are_rejected_before_configuration(role: Role) -> None:
    with pytest.raises(ValueError, match="do not accept extra arguments"):
        plan_command(role, ["private-argument"])


def test_operator_role_does_not_require_migration_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_ALEMBIC_CONFIG", "missing")
    assert plan_command(Role.CLI, ["stats"]).argv[-1] == "stats"
