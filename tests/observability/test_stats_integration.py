import json

import pytest
from sqlalchemy.engine import Engine

from pytask_service import cli_monitoring
from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_cli_and_database_summary_have_matching_counts(
    isolated_engine: Engine, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database = MonitoringDatabase(isolated_engine)
    database.task(status="failed")
    monkeypatch.setattr(cli_monitoring, "build_engine", lambda settings: isolated_engine)
    monkeypatch.delenv("PYTASK_REGISTRY", raising=False)
    assert cli_monitoring.show_stats(60) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["window_seconds"] == 60
    assert payload["queue"]["failed"] == payload["queue"]["total"] == 1
