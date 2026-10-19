import pytest

from pytask_service.benchmarks.arguments import parser, read_options
from pytask_service.benchmarks.options import BenchmarkOptions, Workload


def test_cli_defaults_match_the_validated_plan():
    assert read_options(parser().parse_args([])) == BenchmarkOptions()


def test_custom_plan_preserves_worker_and_workload_order():
    args = parser().parse_args(
        [
            "--tasks",
            "3",
            "--workers",
            "4",
            "1",
            "--repeat",
            "2",
            "--warmup",
            "0",
            "--workloads",
            "checksum",
            "noop",
            "--no-recovery",
        ]
    )
    options = read_options(args)
    assert options.workers == (4, 1)
    assert options.workloads == (Workload.CHECKSUM, Workload.NOOP)
    assert options.tasks == 3
    assert options.recovery is False


@pytest.mark.parametrize(
    "arguments", [["--workers"], ["--tasks", "abc"], ["--workloads", "custom"]]
)
def test_invalid_cli_syntax_exits_before_running(arguments):
    with pytest.raises(SystemExit) as caught:
        parser().parse_args(arguments)
    assert caught.value.code == 2
