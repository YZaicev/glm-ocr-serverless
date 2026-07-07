"""Tests for JSON extraction helpers."""

import pytest

from app.utils.json_utils import extract_json_object


def test_extract_json_object_from_plain_json() -> None:
    payload = extract_json_object('{"full_name":"IVAN IVANOV","document_number":"123"}')
    assert payload["full_name"] == "IVAN IVANOV"


def test_extract_json_object_from_markdown_block() -> None:
    text = '```json\n{"full_name":"IVAN IVANOV"}\n```'
    payload = extract_json_object(text)
    assert payload["full_name"] == "IVAN IVANOV"


def test_extract_json_object_invalid_raises() -> None:
    with pytest.raises(ValueError):
        extract_json_object("not json")
