"""Tests for base64 decoding utilities."""

import base64

import pytest

from app.core.exceptions import InvalidImageException
from app.utils.base64_utils import decode_base64_payload, parse_data_uri


def test_parse_raw_base64_without_data_uri() -> None:
    mime, payload = parse_data_uri("YWJj")
    assert mime is None
    assert payload == "YWJj"


def test_parse_data_uri_with_mime() -> None:
    mime, payload = parse_data_uri("data:image/png;base64,YWJj")
    assert mime == "image/png"
    assert payload == "YWJj"


def test_decode_base64_payload() -> None:
    raw = b"hello"
    encoded = base64.b64encode(raw).decode("ascii")
    assert decode_base64_payload(encoded) == raw


def test_decode_data_uri_payload() -> None:
    raw = b"hello"
    encoded = base64.b64encode(raw).decode("ascii")
    data_uri = f"data:image/jpeg;base64,{encoded}"
    assert decode_base64_payload(data_uri) == raw


def test_decode_invalid_base64_raises() -> None:
    with pytest.raises(InvalidImageException, match="base64"):
        decode_base64_payload("not!!!valid")
