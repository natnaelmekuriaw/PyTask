from dataclasses import replace

import pytest

from pytask_service.benchmarks.cases import CaseSpec
from pytask_service.benchmarks.options import Workload
from pytask_service.benchmarks.results import CaseResult
from pytask_service.benchmarks.summary import summarize


def rows(metrics, workers, values):
    return tuple(
        CaseResult(
            CaseSpec(Workload.NOOP, workers, repetition),
            replace(metrics, throughput_per_second=value),
        )
        for repetition, value in enumerate(values, 1)
    )


def test_summary_uses_median_and_range_of_all_repetitions(metrics):
    baseline = rows(metrics, 1, [2, 10, 3])
    parallel = rows(metrics, 4, [9, 12, 15])
    single, multi = summarize(baseline + parallel, 3)
    assert (
        single.median_throughput,
        single.minimum_throughput,
        single.maximum_throughput,
    ) == (3, 2, 10)
    assert single.speedup == 1
    assert multi.speedup == pytest.approx(4)


def test_missing_or_duplicate_repetitions_have_no_summary(metrics):
    incomplete = rows(metrics, 1, [2, 3])
    duplicate = (incomplete[0], incomplete[0], incomplete[1])
    for results in (incomplete, duplicate):
        summary = summarize(results, 3)[0]
        assert (
            summary.median_throughput
            is summary.minimum_throughput
            is summary.maximum_throughput
            is summary.speedup
            is None
        )


def test_invalid_baseline_prevents_speedup_but_preserves_parallel_results(metrics):
    failed = CaseResult(CaseSpec(Workload.NOOP, 1, 1), error_code="task_failed")
    baseline, parallel = summarize((failed,) + rows(metrics, 2, [8]), 1)
    assert baseline.median_throughput is None
    assert parallel.median_throughput == 8
    assert parallel.speedup is None


def test_parallel_only_plan_has_no_invented_baseline(metrics):
    assert summarize(rows(metrics, 4, [4]), 1)[0].speedup is None
