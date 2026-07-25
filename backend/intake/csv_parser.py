"""Pure-Python parsing for common Indian payment and bank CSV exports."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from intake.types import ExtractedEntryDraft


HEADER_SYNONYMS = {
    "amount": {"amount", "transaction amount", "amount inr", "राशि", "रकम"},
    "debit": {"debit", "dr", "withdrawal", "paid", "debit amount"},
    "credit": {"credit", "cr", "deposit", "received", "credit amount"},
    "date": {"date", "txn date", "transaction date", "txn date time", "तारीख"},
    "upi_ref": {"upi ref", "upi reference", "upi ref no", "transaction id", "utr", "ref no", "यूपीआई रेफ"},
    "party": {"name", "merchant", "transaction details", "description", "narration", "to from", "party", "नाम"},
}


def normalize_header(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    keep = "".join(
        character if (character.isalnum() or character.isspace() or unicodedata.category(character).startswith("M")) else " "
        for character in normalized
    )
    return re.sub(r"\s+", " ", keep).strip()


def _header_map(fieldnames: list[str] | None) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for original in fieldnames or []:
        normalized = normalize_header(original)
        for target, synonyms in HEADER_SYNONYMS.items():
            if normalized in synonyms and target not in mapped:
                mapped[target] = original
    return mapped


def _value(row: dict[str, str | None], headers: dict[str, str], key: str) -> str:
    return (row.get(headers[key]) or "").strip() if key in headers else ""


def _to_paise(value: str) -> tuple[int, bool] | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    negative = cleaned.startswith("-") or (cleaned.startswith("(") and cleaned.endswith(")"))
    cleaned = cleaned.replace("₹", "").replace(",", "").replace("(", "").replace(")", "")
    cleaned = re.sub(r"\b(?:inr|rs\.?)\b", "", cleaned, flags=re.IGNORECASE).strip()
    try:
        rupees = Decimal(cleaned)
    except InvalidOperation:
        return None
    paise = int((abs(rupees) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return paise, negative


def _parse_date(value: str) -> str | None:
    if not value:
        return None
    value = value.strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    return None


def parse_csv_text(text: str, *, store_id: str, source_document_id: str) -> list[ExtractedEntryDraft]:
    """Return normalized, immutable entries; invalid monetary rows are ignored."""
    if not text.strip():
        return []
    reader = csv.DictReader(io.StringIO(text))
    headers = _header_map(reader.fieldnames)
    if not {"amount", "debit", "credit"}.intersection(headers):
        return []

    entries: list[ExtractedEntryDraft] = []
    for row_number, row in enumerate(reader, start=2):
        amount_value = _value(row, headers, "amount")
        debit_value = _value(row, headers, "debit")
        credit_value = _value(row, headers, "credit")
        parsed: tuple[int, bool] | None
        entry_type: str
        if credit_value and (parsed := _to_paise(credit_value)) and parsed[0] > 0:
            entry_type = "payment_in"
        elif debit_value and (parsed := _to_paise(debit_value)) and parsed[0] > 0:
            entry_type = "payment_out"
        else:
            parsed = _to_paise(amount_value)
            if not parsed:
                continue
            entry_type = "payment_out" if parsed[1] else "payment_in"
        amount_paise = parsed[0]
        if amount_paise == 0:
            continue
        party = _value(row, headers, "party") or None
        entries.append(
            ExtractedEntryDraft(
                store_id=store_id,
                source_document_id=source_document_id,
                entry_type=entry_type,
                party_name=party,
                amount_paise=amount_paise,
                entry_date=_parse_date(_value(row, headers, "date")),
                description=party or "CSV transaction",
                confidence=1.0,
                extraction_model="deterministic_parser",
                bbox_or_line_ref=f"row {row_number}",
                upi_ref=_value(row, headers, "upi_ref") or None,
            )
        )
    return entries
