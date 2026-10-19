import pytest

from pytask_service.runtime import probe
from pytask_service.runtime.schema import RuntimeFailure
from tests.deployment.fakes import Engine


@pytest.mark.parametrize("fails", [False, True])
def test_probe_cleanup_does_not_depend_on_schema_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fails: bool,
) -> None:
    engine = Engine()

    def check(database: object, paths: object) -> None:
        if fails:
            raise RuntimeFailure("not current")

    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@postgres/db")
    monkeypatch.setattr(probe, "build_engine", lambda settings: engine)
    monkeypatch.setattr(probe, "check_schema", check)
    if fails:
        with pytest.raises(RuntimeFailure, match="not current"):
            probe.run_probe("database")
        assert capsys.readouterr().out == ""
    else:
        assert probe.run_probe("database") == 0
    assert engine.disposed
