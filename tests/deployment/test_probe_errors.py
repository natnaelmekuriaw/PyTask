from urllib.error import HTTPError, URLError

import pytest

from pytask_service.runtime import http_probe
from pytask_service.runtime.schema import RuntimeFailure


@pytest.mark.parametrize("code", [302, 500, 503])
def test_http_failures_report_status_without_response_details(
    monkeypatch: pytest.MonkeyPatch,
    code: int,
) -> None:
    class Opener:
        def open(self, *args: object, **kwargs: object) -> None:
            raise HTTPError("private-url", code, "private-message", {}, None)

    monkeypatch.setattr(http_probe, "build_opener", lambda *handlers: Opener())
    with pytest.raises(RuntimeFailure) as failure:
        http_probe.probe_api()
    assert str(failure.value) == f"API readiness returned HTTP {code}"


def test_transport_errors_do_not_expose_exception_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Opener:
        def open(self, *args: object, **kwargs: object) -> None:
            raise URLError("private transport information")

    monkeypatch.setattr(http_probe, "build_opener", lambda *handlers: Opener())
    with pytest.raises(RuntimeFailure) as failure:
        http_probe.probe_api()
    assert str(failure.value) == "API readiness check failed"
