from starlette.types import ASGIApp, Message, Receive, Scope, Send

from pytask_service.api.errors import error_response

MAX_REQUEST_BYTES = 128 * 1024


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_REQUEST_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length")
        if length is not None:
            try:
                declared = int(length)
                if declared < 0:
                    raise ValueError
            except ValueError:
                await error_response(
                    400, "invalid_content_length", "Invalid Content-Length"
                )(scope, receive, send)
                return
            if declared > self.max_bytes:
                await self._too_large(scope, receive, send)
                return
        body = bytearray()
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.max_bytes:
                await self._too_large(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        if size and scope["method"] in {"POST", "PUT", "PATCH"}:
            media_type = (
                headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
            )
            if media_type != b"application/json" and not (
                media_type.startswith(b"application/") and media_type.endswith(b"+json")
            ):
                await error_response(
                    415,
                    "unsupported_media_type",
                    "Use an application/json request body",
                )(scope, receive, send)
                return
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    async def _too_large(self, scope: Scope, receive: Receive, send: Send) -> None:
        await error_response(413, "request_too_large", "Request body exceeds 128 KiB")(
            scope, receive, send
        )
