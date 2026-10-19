import json

import pytest

from pytask_service.runtime import probe


def test_api_probe_needs_no_database_settings(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[float] = []
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setenv("PYTASK_PROBE_TIMEOUT_SECONDS", "0.5")
    monkeypatch.setattr(probe, "probe_api", lambda timeout: calls.append(timeout))
    assert probe.run_probe("api") == 0
    assert calls == [0.5]
    assert json.loads(capsys.readouterr().out) == {"status": "ok"}


def test_invalid_probe_kind_never_opens_an_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(settings: object) -> None:
        raise AssertionError("invalid probes must not connect")

    monkeypatch.setattr(probe, "build_engine", unexpected)
    with pytest.raises(ValueError, match="api or database"):
        probe.run_probe("unknown")
