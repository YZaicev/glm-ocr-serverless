"""Tests for MRZ parser."""

from app.services.mrz_parser_service import MrzParserService

_SAMPLE_TD3 = """
P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
L898902C<3UTO6908061F9406236ZE184226B<<<<<14
"""


def test_parse_td3_passport() -> None:
    result = MrzParserService().parse_from_text(_SAMPLE_TD3)
    assert result.parsed is True
    assert result.valid is True
    assert result.format == "TD3"
    assert result.fields is not None
    assert result.fields.document_number == "L898902C"
    assert result.fields.nationality == "UTO"
    assert result.fields.date_of_birth == "1969-08-06"
    assert result.fields.expiry_date == "1994-06-23"


def test_parse_no_mrz_returns_empty() -> None:
    result = MrzParserService().parse_from_text("just some random ocr text")
    assert result.parsed is False
    assert result.valid is False
