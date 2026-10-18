import pytest

from pytask_service.observability.window import ObservationWindow


@pytest.mark.parametrize("seconds", [60, 3600, 604800])
def test_window_accepts_supported_bounds(seconds: int) -> None:
    assert ObservationWindow(seconds).seconds == seconds


@pytest.mark.parametrize("seconds", [True, False, 59, 604801, 60.0, "60", None])
def test_window_rejects_ambiguous_or_unbounded_values(seconds: object) -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        ObservationWindow(seconds)
