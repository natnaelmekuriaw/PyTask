import hashlib

from pytask_service.benchmarks.catalog import work_item
from pytask_service.benchmarks.options import BenchmarkOptions, Workload


def test_noop_and_sleep_payloads_match_handler_parameters():
    options = BenchmarkOptions(sleep_ms=31)
    noop = work_item(Workload.NOOP, 4, options)
    wait = work_item(Workload.SLEEP, 4, options)
    assert (noop.name, noop.arguments, noop.expected) == (
        "benchmark.noop",
        {"index": 4},
        4,
    )
    assert wait.arguments == {"index": 4, "milliseconds": 31}
    assert wait.expected == 4


def test_checksum_reference_is_prepared_with_the_requested_cost():
    item = work_item(Workload.CHECKSUM, 9, BenchmarkOptions(iterations=1))
    assert item.name == "benchmark.checksum"
    assert item.arguments == {"index": 9, "iterations": 1}
    assert item.expected == hashlib.sha256(b"9").hexdigest()
