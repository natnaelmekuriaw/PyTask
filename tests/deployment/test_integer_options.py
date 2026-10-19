import pytest

from pytask_service.env_options import integer_option


@pytest.mark.parametrize("raw", ["0", "10", " 5 "])
def test_supported_integer_values_are_read(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    monkeypatch.setenv("PYTASK_TEST_LIMIT", raw)
    assert integer_option("PYTASK_TEST_LIMIT", 3, minimum=0, maximum=10) == int(raw)


@pytest.mark.parametrize(
    "raw",
    ["", "-1", "+1", "1.0", "1e1", "true", "١", "11", "9" * 1000],
    ids=[
        "empty",
        "negative",
        "signed",
        "float",
        "exponent",
        "boolean",
        "unicode_digit",
        "out_of_range",
        "oversized",
    ],
)
def test_integer_errors_never_echo_values(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    monkeypatch.setenv("PYTASK_TEST_LIMIT", raw)
    with pytest.raises(ValueError) as failure:
        integer_option("PYTASK_TEST_LIMIT", 3, minimum=0, maximum=10)
    assert str(failure.value) == "PYTASK_TEST_LIMIT must be an integer from 0 to 10"
