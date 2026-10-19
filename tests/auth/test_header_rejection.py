import pytest

from pytask_service.auth.headers import AuthenticationError, parse_bearer


def test_multiple_authorization_fields_are_ambiguous() -> None:
    with pytest.raises(AuthenticationError) as error:
        parse_bearer([(b"authorization", b"Bearer one"), (b"Authorization", b"Bearer two")])
    assert error.value.reason == "malformed"


@pytest.mark.parametrize("value", [
    b"", b"Basic abc", b"Bearer", b"Bearer\tabc", b" Bearer abc", b"Bearer abc ",
    b"Bearer abc, Bearer def", b"Bearer a\r\nb", b"Bearer \xff", b"Bearer " + b"x" * 129,
])
def test_invalid_header_values_never_escape_in_errors(value: bytes) -> None:
    with pytest.raises(AuthenticationError) as error:
        parse_bearer([(b"authorization", value)])
    assert error.value.reason == "invalid"
    assert "abc" not in str(error.value)

