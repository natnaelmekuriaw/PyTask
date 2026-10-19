from collections.abc import Mapping

from fastapi.responses import JSONResponse

from pytask_service.api.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse


class APIError(Exception):
    def __init__(
        self, status: int, code: str, message: str,
        *, headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.headers = headers


def error_response(
    status: int,
    code: str,
    message: str,
    *,
    details: list[ErrorDetail] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details or [])
    )
    return JSONResponse(
        body.model_dump(mode="json"), status_code=status, headers=headers
    )
