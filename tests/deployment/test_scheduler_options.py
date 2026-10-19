import pytest

from pytask_service.runtime.scheduler_options import SchedulerOptions


@pytest.mark.parametrize(
    "name,raw",
    [
        ("PYTASK_SCHEDULER_BATCH_SIZE", "0"),
        ("PYTASK_SCHEDULER_BATCH_SIZE", "1001"),
        ("PYTASK_SCHEDULER_POLL_SECONDS", "inf"),
    ],
)
def test_invalid_scheduler_configuration_fails_early(
    monkeypatch: pytest.MonkeyPatch, name: str, raw: str
) -> None:
    monkeypatch.setenv(name, raw)
    with pytest.raises(ValueError, match=name):
        SchedulerOptions.from_env()


def test_scheduler_does_not_parse_unrelated_api_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTASK_API_CONCURRENCY", "invalid")
    monkeypatch.setenv("PYTASK_SCHEDULER_BATCH_SIZE", "20")
    assert SchedulerOptions.from_env().batch_size == 20
