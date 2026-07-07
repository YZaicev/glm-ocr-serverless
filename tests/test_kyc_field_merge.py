"""Tests for KYC field merge."""

from app.schemas.kyc.document import KycFields
from app.services.kyc_field_merge import merge_kyc_fields


def test_merge_mrz_overrides_llm() -> None:
    llm = KycFields(full_name="WRONG NAME", city="Moscow")
    mrz = KycFields(full_name="ANNA MARIA ERIKSSON", document_number="L898902C")
    merged = merge_kyc_fields(llm, mrz)
    assert merged.full_name == "ANNA MARIA ERIKSSON"
    assert merged.document_number == "L898902C"
    assert merged.city == "Moscow"
