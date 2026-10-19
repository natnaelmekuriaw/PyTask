import pytest

from pytask_service.runtime import http_probe
from pytask_service.runtime.schema import RuntimeFailure


class Response:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self.body, self.status = body, status
        self.read_limit = 0

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def read(self, limit: int) -> bytes:
        self.read_limit = limit
        return self.body[:limit]


class Opener:
    def __init__(self, response: Response) -> None:
        self.response = response
        self.calls: list[tuple[str, float]] = []

    def open(self, url: str, *, timeout: float) -> Response:
        self.calls.append((url, timeout))
        return self.response


@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b"true",
        b'{"status":"bad"}',
        b'{"status":"ok","private":"extra"}',
        b"\xff",
        b"x" * 1025,
    ],
)
def test_invalid_probe_responses_are_rejected_without_echoing_content(
    monkeypatch: pytest.MonkeyPatch,
    body: bytes,
) -> None:
    response = Response(body)
    monkeypatch.setattr(http_probe, "build_opener", lambda *handlers: Opener(response))
    with pytest.raises(RuntimeFailure) as failure:
        http_probe.probe_api()
    assert "private" not in str(failure.value)
    assert response.read_limit == 1025


def test_successful_probe_uses_only_the_loopback_readiness_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opener = Opener(Response(b'{"status":"ok"}'))
    monkeypatch.setattr(http_probe, "build_opener", lambda *handlers: opener)
    http_probe.probe_api(0.5)
    assert opener.calls == [("http://127.0.0.1:8000/health/ready", 0.5)]
