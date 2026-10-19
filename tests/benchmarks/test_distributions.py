import pytest

from pytask_service.benchmarks.distributions import distribution


def test_empty_distribution_has_no_synthetic_zeroes():
    result = distribution([])
    assert result.samples == 0
    assert result.mean is result.p50 is result.p95 is result.p99 is None


def test_single_sample_percentiles_are_the_sample():
    result = distribution([0.25])
    assert (
        result.p50
        == result.p95
        == result.p99
        == result.minimum
        == result.maximum
        == 0.25
    )


def test_percentiles_interpolate_sorted_samples():
    result = distribution(iter([10.0, 0.0, 5.0]))
    assert result.samples == 3
    assert result.mean == result.p50 == 5
    assert result.p95 == pytest.approx(9.5)
    assert result.p99 == pytest.approx(9.9)


@pytest.mark.parametrize("value", [-1, float("inf"), float("-inf"), float("nan")])
def test_invalid_timing_samples_are_rejected(value):
    with pytest.raises(ValueError):
        distribution([0.0, value])
