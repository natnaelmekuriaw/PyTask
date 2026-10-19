import asyncio
from types import SimpleNamespace

from starlette.types import Message, Receive, Scope, Send

from pytask_service.api.auth_middleware import AuthenticationMiddleware
from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.settings import AuthSettings
from pytask_service.auth.store import KeyStore


def test_an_unauthenticated_upload_is_not_read(key: IssuedKey) -> None:
    async def request() -> list[Message]:
        sent: list[Message] = []

        async def receive() -> Message:
            raise AssertionError("unauthenticated body was consumed")

        async def send(message: Message) -> None:
            sent.append(message)

        async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
            raise AssertionError("unauthenticated request reached the application")

        state = SimpleNamespace(
            auth_settings=AuthSettings(keys=(key.credential,)),
            auth_store=KeyStore((key.credential,)),
        )
        await AuthenticationMiddleware(downstream)(
            {
                "type": "http",
                "path": "/api/v1/tasks",
                "method": "POST",
                "headers": [(b"content-length", b"999999999")],
                "app": SimpleNamespace(state=state),
            },
            receive,
            send,
        )
        return sent

    assert asyncio.run(request())[0]["status"] == 401
