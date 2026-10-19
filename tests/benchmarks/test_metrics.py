import pytest

from pytask_service.benchmarks.metrics import measure


def test_task_throughput_uses_the_full_observation_window(observation):
    metrics = measure(observation, 4.0, 0.5)
    assert metrics.submitted == metrics.succeeded == metrics.attempts == 2
    assert metrics.failed == 0
    assert metrics.throughput_per_second == 0.5
    assert metrics.submissions_per_second == 4


def test_latency_queue_wait_and_attempt_duration_are_separate(observation):
    metrics = measure(observation, 4.0, 0.5)
    assert metrics.latency_seconds.p95 == 3
    assert metrics.queue_wait_seconds.p95 == 1
    assert metrics.attempt_seconds.p95 == 2


@pytest.mark.parametrize(
    "elapsed,submission",
    [
        (0, 0.1),
        (1, 0),
        (1, 2),
        (float("nan"), 1),
        (1, float("inf")),
        (True, 0.5),
        (1, False),
        ("1", 0.5),
    ],
)
def test_invalid_measurement_windows_are_rejected(observation, elapsed, submission):
    with pytest.raises(RuntimeError, match="invalid_elapsed_time"):
        measure(observation, elapsed, submission)
