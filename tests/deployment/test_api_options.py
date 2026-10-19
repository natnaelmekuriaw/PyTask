import pytest

from pytask_service.runtime.api_options import APIOptions


@pytest.mark.parametrize(
    "name,raw",
    [
        ("PYTASK_API_GRACEFUL_SECONDS", "0"),
        ("PYTASK_API_GRACEFUL_SECONDS", "301"),
        ("PYTASK_API_CONCURRENCY", "10001"),
        ("PYTASK_API_KEEP_ALIVE_SECONDS", "61"),
    ],
)
def test_invalid_api_limits_are_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str, raw: str
) -> None:
    monkeypatch.setenv(name, raw)
    with pytest.raises(ValueError, match=name):
        APIOptions.from_env()


def test_api_limits_are_independent_of_worker_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_API_CONCURRENCY", "200")
    monkeypatch.setenv("PYTASK_WORKER_LEASE_SECONDS", "invalid")
    assert APIOptions.from_env().concurrency == 200
