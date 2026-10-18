import asyncio
import json

import pytest
from starlette.responses import JSONResponse
from starlette.types import Message, Receive, Scope, Send

from pytask_service.api.body_limit import BodyLimitMiddleware


def send_chunks(chunks: list[bytes], headers: list[tuple[bytes, bytes]]) -> tuple[int, dict[str, object]]:
    async def request() -> tuple[int, dict[str, object]]:
        incoming = iter([{"type": "http.request", "body": chunk, "more_body": index < len(chunks) - 1} for index, chunk in enumerate(chunks)])
        sent: list[Message] = []
        async def receive() -> Message:
            return next(incoming, {"type": "http.disconnect"})
        async def send(message: Message) -> None:
            sent.append(message)
        async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
            message = await receive()
            await JSONResponse({"bytes": len(message["body"])})(scope, receive, send)
        scope: Scope = {"type": "http", "method": "POST", "headers": headers}
        await BodyLimitMiddleware(downstream, max_bytes=8)(scope, receive, send)
        return sent[0]["status"], json.loads(sent[1]["body"])
    return asyncio.run(request())


def test_actual_stream_size_is_checked_without_content_length() -> None:
    status, body = send_chunks([b"1234", b"56789"], [(b"content-type", b"application/json")])
    assert status == 413 and body["error"]["code"] == "request_too_large"


def test_declared_oversize_body_is_rejected_before_reading() -> None:
    assert send_chunks([], [(b"content-length", b"9")])[0] == 413
