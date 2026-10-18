from pytask_service.worker.outcome import MAX_ERROR_CHARS, TaskOutcome


def test_success_keeps_a_json_result() -> None:
    outcome = TaskOutcome.success({"items": [1, 2, 3]})

    assert outcome.succeeded
    assert outcome.result == {"items": [1, 2, 3]}
    assert outcome.error is None


def test_failure_keeps_exception_context() -> None:
    try:
        raise RuntimeError("something broke")
    except RuntimeError as error:
        outcome = TaskOutcome.failure(error)

    assert not outcome.succeeded
    assert outcome.result is None
    assert outcome.error is not None
    assert "RuntimeError: something broke" in outcome.error


def test_failure_detail_is_bounded() -> None:
    outcome = TaskOutcome.failure(RuntimeError("x" * (MAX_ERROR_CHARS * 2)))

    assert outcome.error is not None
    assert len(outcome.error) <= MAX_ERROR_CHARS + 5


def test_missing_process_result_records_exit_code() -> None:
    outcome = TaskOutcome.process_exit(9)

    assert not outcome.succeeded
    assert outcome.error is not None
    assert "exit code 9" in outcome.error


def test_timeout_is_distinct_from_handler_failure() -> None:
    outcome = TaskOutcome.timeout(5)

    assert not outcome.succeeded
    assert outcome.timed_out
    assert outcome.error == "Execution exceeded 5 seconds"
