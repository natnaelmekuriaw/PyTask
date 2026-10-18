import asyncio
import json

import pytest
from starlette.responses import JSONResponse
from starlette.types import Message, Receive, Scope, Send

from pytask_service.api.body_limit import BodyLimitMiddleware


def send_chunks(
    chunks: list[bytes], headers: list[tuple[bytes, bytes]]
) -> tuple[int, dict[str, object]]:
    async def request() -> tuple[int, dict[str, object]]:
        incoming = iter(
            [
                {
                    "type": "http.request",
                    "body": chunk,
                    "more_body": index < len(chunks) - 1,
                }
                for index, chunk in enumerate(chunks)
            ]
        )
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
    status, body = send_chunks(
        [b"1234", b"56789"], [(b"content-type", b"application/json")]
    )
    assert status == 413 and body["error"]["code"] == "request_too_large"


def test_declared_oversize_body_is_rejected_before_reading() -> None:
    assert send_chunks([], [(b"content-length", b"9")])[0] == 413


@pytest.mark.parametrize("length", [b"-1", b"abc", b"+1", b"1_0", b"-0"])
def test_invalid_content_length_has_a_public_error(length: bytes) -> None:
    assert send_chunks([], [(b"content-length", length)])[0] == 400


@pytest.mark.parametrize(
    "media_type",
    [
        b"application/json",
        b"Application/JSON; charset=utf-8",
        b"application/example+json",
    ],
)
def test_json_media_types_and_exact_size_bodies_are_accepted(media_type: bytes) -> None:
    assert send_chunks([b"1234", b"5678"], [(b"content-type", media_type)]) == (
        200,
        {"bytes": 8},
    )


def test_bodyless_controls_need_no_content_type() -> None:
    assert send_chunks([b""], []) == (200, {"bytes": 0})
    assert send_chunks([b"{}"], [(b"content-type", b"text/plain")])[0] == 415
