import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from pytask_service.api.cursors import InvalidCursor
from pytask_service.api.errors import APIError, error_response
from pytask_service.api.schemas.errors import ErrorDetail
from pytask_service.arguments import InvalidTaskArguments
from pytask_service.registry import UnknownTaskError
from pytask_service.scheduling.definitions import ScheduleNotFound

logger = logging.getLogger(__name__)


def register_errors(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def handle_api(request: Request, error: APIError) -> JSONResponse:
        return error_response(error.status, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, error: RequestValidationError) -> JSONResponse:
        errors = error.errors()
        if any(item["type"] == "json_invalid" for item in errors):
            return error_response(400, "invalid_json", "Request body must contain valid JSON")
        details = [ErrorDetail(location=list(item["loc"]), message=item["msg"], type=item["type"]) for item in errors]
        return error_response(422, "invalid_request", "Request validation failed", details=details)

    @app.exception_handler(UnknownTaskError)
    async def handle_unknown_task(request: Request, error: UnknownTaskError) -> JSONResponse:
        return error_response(422, "unknown_task", str(error))

    @app.exception_handler(InvalidTaskArguments)
    async def handle_arguments(request: Request, error: InvalidTaskArguments) -> JSONResponse:
        return error_response(422, "invalid_arguments", str(error))

    @app.exception_handler(InvalidCursor)
    async def handle_cursor(request: Request, error: InvalidCursor) -> JSONResponse:
        return error_response(422, "invalid_cursor", str(error))

    @app.exception_handler(ScheduleNotFound)
    async def handle_schedule_missing(request: Request, error: ScheduleNotFound) -> JSONResponse:
        return error_response(404, "schedule_not_found", str(error))

    @app.exception_handler(HTTPException)
    async def handle_http(request: Request, error: HTTPException) -> JSONResponse:
        code = {404: "not_found", 405: "method_not_allowed"}.get(error.status_code, "http_error")
        message = {404: "Resource not found", 405: "Method not allowed"}.get(error.status_code, "Request could not be completed")
        return error_response(error.status_code, code, message, headers=error.headers)

    @app.exception_handler(IntegrityError)
    async def handle_integrity(request: Request, error: IntegrityError) -> JSONResponse:
        constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if constraint == "uq_schedules_name":
            return error_response(409, "schedule_name_conflict", "Schedule name already exists")
        logger.error("API integrity failure", exc_info=(type(error), error, error.__traceback__))
        return error_response(500, "internal_error", "An internal error occurred")

    @app.exception_handler(SQLAlchemyError)
    async def handle_database(request: Request, error: SQLAlchemyError) -> JSONResponse:
        logger.error("API database failure", exc_info=(type(error), error, error.__traceback__))
        return error_response(503, "database_unavailable", "Database is unavailable")

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, error: Exception) -> JSONResponse:
        logger.error("Unhandled API failure", exc_info=(type(error), error, error.__traceback__))
        return error_response(500, "internal_error", "An internal error occurred")
