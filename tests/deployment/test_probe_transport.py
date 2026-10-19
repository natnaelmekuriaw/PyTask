from email.message import Message
from io import BytesIO
from urllib.request import ProxyHandler, Request

import pytest

from pytask_service.runtime import http_probe
from tests.deployment.test_http_probe import Opener, Response


def test_probe_installs_explicit_no_proxy_and_no_redirect_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []

    def build(*handlers: object) -> Opener:
        captured.extend(handlers)
        return Opener(Response(b'{"status":"ok"}'))

    monkeypatch.setenv("HTTP_PROXY", "http://private-proxy.invalid")
    monkeypatch.setattr(http_probe, "build_opener", build)
    http_probe.probe_api()
    proxy = next(item for item in captured if isinstance(item, ProxyHandler))
    assert proxy.proxies == {}
    redirect = next(
        item for item in captured if isinstance(item, http_probe.NoRedirect)
    )
    assert (
        redirect.redirect_request(
            Request("http://127.0.0.1:8000/health/ready"),
            BytesIO(),
            302,
            "redirect",
            Message(),
            "http://private-endpoint.invalid",
        )
        is None
    )
