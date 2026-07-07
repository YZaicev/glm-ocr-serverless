"""MRZ extraction and parsing from OCR text (ICAO 9303)."""

from __future__ import annotations

import re
from typing import Final

from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td2 import TD2CodeChecker
from mrz.checker.td3 import TD3CodeChecker

from app.schemas.kyc.document import KycFields
from app.schemas.kyc.mrz import MrzParseResult
from app.utils.logging import get_logger

logger = get_logger(__name__)

_MRZ_CHARSET: Final[set[str]] = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")
_TD3_LEN: Final[int] = 44
_TD2_LEN: Final[int] = 36
_TD1_LEN: Final[int] = 30


class MrzParserService:
    """Parse MRZ lines from OCR output."""

    def parse_from_text(self, text: str) -> MrzParseResult:
        lines = _normalize_lines(text)
        candidates = _find_mrz_candidates(lines)
        for fmt, block in candidates:
            result = _parse_block(fmt, block)
            if result.parsed:
                return result
        return MrzParseResult()

    def parse_from_pages(self, pages: list[dict[str, object]]) -> MrzParseResult:
        chunks: list[str] = []
        for page in pages:
            chunks.append(str(page.get("text", "")))
        return self.parse_from_text("\n".join(chunks))


def _normalize_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        cleaned = re.sub(r"[^A-Za-z0-9<]", "", raw).upper()
        if cleaned:
            lines.append(cleaned)
    return lines


def _find_mrz_candidates(lines: list[str]) -> list[tuple[str, list[str]]]:
    candidates: list[tuple[str, list[str]]] = []

    for index in range(len(lines) - 1):
        pair = [lines[index], lines[index + 1]]
        if _is_mrz_line(pair[0], _TD3_LEN) and _is_mrz_line(pair[1], _TD3_LEN):
            candidates.append(("TD3", pair))
        if _is_mrz_line(pair[0], _TD2_LEN) and _is_mrz_line(pair[1], _TD2_LEN):
            candidates.append(("TD2", pair))

    for index in range(len(lines) - 2):
        triple = [lines[index], lines[index + 1], lines[index + 2]]
        if all(_is_mrz_line(line, _TD1_LEN) for line in triple):
            candidates.append(("TD1", triple))

    return candidates


def _is_mrz_line(line: str, length: int) -> bool:
    return len(line) == length and all(char in _MRZ_CHARSET for char in line)


def _parse_block(fmt: str, lines: list[str]) -> MrzParseResult:
    block = "\n".join(lines)
    try:
        if fmt == "TD3":
            checker = TD3CodeChecker(block, check_expiry=False)
        elif fmt == "TD2":
            checker = TD2CodeChecker(block, check_expiry=False)
        else:
            checker = TD1CodeChecker(block, check_expiry=False)
    except Exception:
        logger.debug("MRZ block rejected by checker", exc_info=True)
        return MrzParseResult(raw_lines=lines)

    if not checker:
        return MrzParseResult(parsed=True, valid=False, format=fmt, raw_lines=lines)

    fields_obj = checker.fields()
    fields_data = fields_obj._asdict() if hasattr(fields_obj, "_asdict") else dict(fields_obj)
    fields = _map_mrz_fields(fields_data)
    return MrzParseResult(
        parsed=True,
        valid=True,
        format=fmt,
        fields=fields,
        raw_lines=lines,
        confidence=0.95,
    )


def _map_mrz_fields(fields_data: object) -> KycFields:
    data = {str(key): value for key, value in dict(fields_data).items()}
    surname = _clean_mrz_name(data.get("surname"))
    given_names = _clean_mrz_name(data.get("name"))
    full_name = " ".join(part for part in (given_names, surname) if part) or None

    return KycFields(
        full_name=full_name,
        first_name=given_names,
        last_name=surname,
        date_of_birth=_mrz_date_to_iso(str(data.get("birth_date", ""))),
        document_number=_none_if_empty(str(data.get("document_number", ""))),
        nationality=_none_if_empty(str(data.get("nationality", ""))),
        issuing_country=_none_if_empty(str(data.get("country", ""))),
        expiry_date=_mrz_date_to_iso(str(data.get("expiry_date", ""))),
        gender=_none_if_empty(str(data.get("sex", ""))),
    )


def _clean_mrz_name(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).replace("<", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def _none_if_empty(value: str) -> str | None:
    cleaned = value.strip()
    return cleaned or None


def _mrz_date_to_iso(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 6:
        return None
    yy = int(digits[0:2])
    mm = int(digits[2:4])
    dd = int(digits[4:6])
    if mm < 1 or mm > 12 or dd < 1 or dd > 31:
        return None
    year = 1900 + yy if yy > 30 else 2000 + yy
    return f"{year:04d}-{mm:02d}-{dd:02d}"
