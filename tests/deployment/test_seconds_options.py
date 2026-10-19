import pytest

from pytask_service.env_options import seconds_option


@pytest.mark.parametrize("raw", ["nan", "inf", "-inf", "0", "-1", "61", "private"])
def test_duration_errors_are_bounded_and_safe(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    monkeypatch.setenv("PYTASK_TEST_SECONDS", raw)
    with pytest.raises(ValueError) as failure:
        seconds_option("PYTASK_TEST_SECONDS", 5, minimum=0.1, maximum=60)
    assert str(failure.value) == "PYTASK_TEST_SECONDS must be finite and from 0.1 to 60"


def test_fractional_durations_and_defaults_remain_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTASK_TEST_SECONDS", raising=False)
    assert seconds_option("PYTASK_TEST_SECONDS", 5, minimum=0.1, maximum=60) == 5
    monkeypatch.setenv("PYTASK_TEST_SECONDS", " 0.25 ")
    assert seconds_option("PYTASK_TEST_SECONDS", 5, minimum=0.1, maximum=60) == 0.25
