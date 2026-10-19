import pytest

from pytask_service.auth.headers import parse_bearer
from pytask_service.auth.issuance import IssuedKey


@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER", "BeArEr"])
def test_bearer_scheme_is_case_insensitive(key: IssuedKey, scheme: str) -> None:
    assert (
        parse_bearer([(b"Authorization", f"{scheme} {key.token}".encode())])
        == key.token
    )


def test_unrelated_headers_do_not_supply_credentials() -> None:
    from pytask_service.auth.headers import AuthenticationError

    with pytest.raises(AuthenticationError) as error:
        parse_bearer([(b"x-api-key", b"not-supported")])
    assert error.value.reason == "missing"
