import logging
from time import monotonic
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from pytask_service.observability.context import bind_context
from pytask_service.observability.events import log_event

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(
        self, app: ASGIApp, route_templates: dict[int, str] | None = None
    ) -> None:
        self.app = app
        self.route_templates = route_templates or {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid4().hex
        scope["pytask.request_id"] = request_id
        status: int | None = None
        error_type: str | None = None
        started = monotonic()

        async def observe(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != b"x-request-id"
                ]
                message = {
                    **message,
                    "headers": [
                        *headers,
                        (b"x-request-id", request_id.encode("ascii")),
                    ],
                }
            await send(message)

        with bind_context(request_id=request_id):
            try:
                await self.app(scope, receive, observe)
            except BaseException as error:
                error_type = type(error).__name__
                if isinstance(error, Exception) and status is None:
                    status = 500
                raise
            finally:
                selected = scope.get("route")
                route = self.route_templates.get(
                    id(selected), getattr(selected, "path", "unmatched")
                )
                method = scope.get("method", "OTHER")
                if method not in {
                    "GET",
                    "HEAD",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                    "OPTIONS",
                }:
                    method = "OTHER"
                log_event(
                    logger,
                    "http.request",
                    level=logging.WARNING
                    if error_type or (status or 0) >= 500
                    else logging.INFO,
                    method=method,
                    route=route,
                    status_code=status,
                    duration_seconds=round(max(0.0, monotonic() - started), 6),
                    error_type=error_type,
                )
