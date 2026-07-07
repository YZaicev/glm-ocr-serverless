"""Merge KYC field dictionaries with MRZ priority."""

from __future__ import annotations

from app.schemas.kyc.document import KycFields


def merge_kyc_fields(*sources: KycFields | None) -> KycFields:
    """Merge fields left-to-right; later non-null values override earlier ones."""
    merged: dict[str, str | None] = {}
    for source in sources:
        if source is None:
            continue
        for key, value in source.model_dump().items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            merged[key] = value
    return KycFields.model_validate(merged)
