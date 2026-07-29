"""Evidence Passport assembly (SPEC §9).

Turns a reconciliation result into the payload the drawer renders: for a ledger entry,
every source that supports it, what each source said, how confident the extractor was,
which model produced it, and why the match was made — in plain language, bilingually.

This module maps engine records to presentation. It performs no arithmetic on money: the
paise integers come straight from the engine, and are only formatted for display.
"""
from __future__ import annotations

from dataclasses import dataclass

from engine.exception_text import format_paise
from engine.types import Entry, ReconciliationResult


@dataclass(frozen=True)
class SourceDescriptor:
    kind: str
    filename: str
    model: str
    confidence: float


# The seeded demo's provenance. `model` is what actually produced the extraction:
# the CSV is parsed by code, so it is honestly labelled `deterministic_parser`.
SOURCE_CATALOGUE: dict[str, SourceDescriptor] = {
    "khaata-page-1": SourceDescriptor("khaata_photo", "khaata_page_1.jpg", "gpt-4o", 1.0),
    "khaata-page-2": SourceDescriptor("khaata_photo", "khaata_page_2.jpg", "gpt-4o", 1.0),
    "invoice-INV-231": SourceDescriptor("invoice_image", "mehta_inv_231.jpg", "gpt-4o", 1.0),
    "invoice-INV-232": SourceDescriptor("invoice_image", "kumar_inv_232.jpg", "gpt-4o", 1.0),
    "invoice-INV-233": SourceDescriptor("invoice_image", "kumar_inv_233.jpg", "gpt-4o", 1.0),
    "july-upi": SourceDescriptor("upi_csv", "july_upi.csv", "deterministic_parser", 1.0),
}
UNKNOWN_SOURCE = SourceDescriptor("manual", "manual_entry", "user", 1.0)

MATCH_RULE_PLAIN: dict[str, tuple[str, str]] = {
    "exact_ref": (
        "Matched because both records carry the same reference number.",
        "मिलान इसलिए हुआ क्योंकि दोनों रिकॉर्ड में एक ही संदर्भ संख्या है।",
    ),
    "exact_amount_date": (
        "Matched because the amount and date are identical.",
        "मिलान इसलिए हुआ क्योंकि राशि और तारीख बिल्कुल एक जैसी हैं।",
    ),
    "amount_within_window": (
        "Matched because the amount is identical and the dates are within three days.",
        "मिलान इसलिए हुआ क्योंकि राशि एक जैसी है और तारीखें तीन दिन के भीतर हैं।",
    ),
    "fuzzy_party_amount": (
        "Matched because the amount is identical and the party names are the same name written differently.",
        "मिलान इसलिए हुआ क्योंकि राशि एक जैसी है और पार्टी का नाम एक ही है, बस अलग तरह से लिखा है।",
    ),
    "voice_confirmed": (
        "Matched because your voice note names the same party and amount.",
        "मिलान इसलिए हुआ क्योंकि आपके वॉइस नोट में वही पार्टी और वही राशि है।",
    ),
}
NO_MATCH_PLAIN = (
    "No matching record was found in any other source yet.",
    "अभी तक किसी और स्रोत में मिलता-जुलता रिकॉर्ड नहीं मिला।",
)


def describe_source(source_id: str) -> SourceDescriptor:
    return SOURCE_CATALOGUE.get(source_id, UNKNOWN_SOURCE)


def source_ref(entry: Entry) -> str:
    """Where inside the source this entry came from — the Evidence Passport `ref`."""
    if entry.upi_ref:
        return f"UPI ref {entry.upi_ref}"
    if entry.source_kind == "khaata_photo":
        return f"page 1, row {entry.id.rsplit('-', 1)[-1]}"
    return "full page"


def source_card(entry: Entry) -> dict[str, object]:
    descriptor = describe_source(entry.source_id)
    return {
        "kind": descriptor.kind,
        "filename": descriptor.filename,
        "ref": source_ref(entry),
        "extracted": {
            "amount": format_paise(entry.amount_paise),
            "party": entry.party_name,
            "date": entry.entry_date,
            "upi_ref": entry.upi_ref,
        },
        "confidence": descriptor.confidence,
        "model": descriptor.model,
        "entry_id": entry.id,
        "source_id": entry.source_id,
    }


def evidence_for(result: ReconciliationResult, ledger_entry_id: str) -> dict[str, object] | None:
    """Assemble the passport for one ledger entry, or None when it does not exist."""
    by_id = {item.id: item for item in result.ledger_entries}
    entry = by_id.get(ledger_entry_id)
    if entry is None:
        return None

    match = next(
        (item for item in result.matches if ledger_entry_id in {item.left_id, item.right_id}),
        None,
    )
    sources = [source_card(entry)]
    if match is not None:
        other_id = match.right_id if match.left_id == ledger_entry_id else match.left_id
        counterpart = by_id.get(other_id)
        if counterpart is not None:
            sources.append(source_card(counterpart))

    plain_en, plain_hi = MATCH_RULE_PLAIN.get(match.match_rule, NO_MATCH_PLAIN) if match else NO_MATCH_PLAIN
    return {
        "ledger_entry_id": ledger_entry_id,
        "ledger_entry": {
            "amount": format_paise(entry.amount_paise),
            "amount_paise": entry.amount_paise,
            "party": entry.party_name,
            "date": entry.entry_date,
            "type": entry.entry_type,
            "description": entry.description,
        },
        "sources": sources,
        "match_rule": match.match_rule if match else None,
        "match_score": match.match_score if match else None,
        "match_rule_plain_en": plain_en,
        "match_rule_plain_hi": plain_hi,
        "status": "verified" if match else "pending_confirmation",
    }


def evidence_files_for(result: ReconciliationResult, ledger_entry_id: str) -> str:
    """Semicolon-joined source filenames, for the CSV export's evidence column."""
    passport = evidence_for(result, ledger_entry_id)
    if not passport:
        return ""
    return ";".join(str(source["filename"]) for source in passport["sources"])  # type: ignore[index]
