from pytask_service.worker.outcome import TaskOutcome


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
