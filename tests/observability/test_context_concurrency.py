import asyncio

from pytask_service.observability.context import bind_context, current_context


def test_concurrent_requests_keep_their_own_identifiers() -> None:
    async def request(identifier: str) -> str:
        with bind_context(request_id=identifier):
            await asyncio.sleep(0)
            return current_context()["request_id"]

    async def run() -> list[str]:
        return await asyncio.gather(request("first"), request("second"))

    assert asyncio.run(run()) == ["first", "second"]
    assert current_context() == {}
