import traceback
from dataclasses import dataclass

from pytask_service.json_value import normalize_json_value

MAX_ERROR_CHARS = 16 * 1024


@dataclass(frozen=True, slots=True)
class TaskOutcome:
    succeeded: bool
    result: object | None = None
    error: str | None = None
    timed_out: bool = False

    @classmethod
    def success(cls, value: object) -> "TaskOutcome":
        return cls(
            succeeded=True, result=normalize_json_value(value, label="Task result")
        )

    @classmethod
    def failure(cls, error: BaseException) -> "TaskOutcome":
        detail = "".join(traceback.format_exception(error))
        if len(detail) > MAX_ERROR_CHARS:
            detail = (
                detail[: MAX_ERROR_CHARS // 2]
                + "\n...\n"
                + detail[-MAX_ERROR_CHARS // 2 :]
            )
        return cls(succeeded=False, error=detail)

    @classmethod
    def process_exit(cls, exit_code: int | None) -> "TaskOutcome":
        return cls(
            succeeded=False,
            error=f"Task process exited without a result (exit code {exit_code})",
        )

    @classmethod
    def timeout(cls, seconds: float) -> "TaskOutcome":
        return cls(
            succeeded=False,
            error=f"Execution exceeded {seconds:g} seconds",
            timed_out=True,
        )
