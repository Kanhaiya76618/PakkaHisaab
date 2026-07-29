"""Pure, deterministic reconciliation over normalized source entries."""
from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

from engine.matchers import match_entries
from engine.accounting import store_total_paise
from engine.exception_text import summarize
from engine.types import Entry, EntryMatch, ExceptionRecord, ReconciliationResult

INVOICE_KIND = "invoice"


def build_exception(kind: str, related: tuple[str, ...], amount_paise: int, party_name: str | None = None) -> ExceptionRecord:
    """Every exception is constructed here so none can ship without amount and copy."""
    summary_en, summary_hi, action = summarize(kind, amount_paise, party_name)
    return ExceptionRecord(kind, related, amount_paise, summary_en, summary_hi, action, party_name)


def detect_duplicate_pairs(entries: list[Entry]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    ordered = sorted(entries, key=lambda item: item.id)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            eligible = (left.source_id.startswith("invoice-") and right.source_id.startswith("invoice-")) or (left.source_id.startswith("source-") and right.source_id.startswith("source-"))
            if not eligible or left.source_id == right.source_id or left.amount_paise != right.amount_paise:
                continue
            if left.party_name and left.party_name.casefold() == (right.party_name or "").casefold():
                from datetime import date
                if abs((date.fromisoformat(left.entry_date) - date.fromisoformat(right.entry_date)).days) <= 1:
                    pairs.append((left.id, right.id))
    return pairs


def reconcile(entries: list[Entry]) -> ReconciliationResult:
    ordered = sorted(entries, key=lambda item: (item.entry_date, item.id))
    matches: list[EntryMatch] = []
    used: set[str] = set()
    for index, left in enumerate(ordered):
        if left.id in used:
            continue
        for right in ordered[index + 1 :]:
            if right.id in used:
                continue
            found = match_entries(left, right)
            if found:
                matches.append(found); used.update((left.id, right.id)); break
    by_id = {item.id: item for item in ordered}
    exceptions: list[ExceptionRecord] = []
    unmatched = tuple(item.id for item in ordered if item.id not in used)
    for identifier in unmatched:
        entry = by_id[identifier]
        if entry.source_kind == INVOICE_KIND:
            exceptions.append(build_exception("unmatched_invoice", (identifier,), entry.amount_paise, entry.party_name))
    for left, right in detect_duplicate_pairs(ordered):
        exceptions.append(build_exception("possible_duplicate", (left, right), by_id[left].amount_paise, by_id[left].party_name))
    for entry in ordered:
        if entry.personal:
            exceptions.append(build_exception("personal_vs_business", (entry.id,), entry.amount_paise, entry.party_name))
    ledger_entries = tuple(ordered)
    return ReconciliationResult(ledger_entries, tuple(matches), tuple(exceptions), unmatched, store_total_paise(ledger_entries))


def reconcile_sample_data(root: Path) -> ReconciliationResult:
    fixture = json.loads((root / "fixtures" / "vision_khaata.json").read_text())["entries"]
    entries: list[Entry] = []
    written_total = 0
    row_total = 0
    for index, raw in enumerate(fixture, 1):
        amount = int(Decimal(str(raw["amount_rupees"])) * 100)
        if raw["description"] == "written_total": written_total = amount; continue
        row_total += amount
        entries.append(Entry(f"khaata-{index}", "khaata-page-1", raw["entry_type"], raw["party_name"], amount, raw["entry_date"], source_kind="khaata_photo", description=raw["description"]))
    invoices = [("invoice-INV-231", "Gupta Traders", 480000, "2026-07-12"), ("invoice-INV-232", "Kumar Suppliers", 720000, "2026-07-10"), ("invoice-INV-233", "Kumar Suppliers", 720000, "2026-07-11")]
    entries += [Entry(identifier, identifier, "purchase", party, amount, day, source_kind=INVOICE_KIND) for identifier, party, amount, day in invoices]
    with (root / "july_upi.csv").open() as file:
        for row in csv.DictReader(file):
            amount = int(Decimal(row["Amount"]) * 100)
            personal = row["UPI Ref"] == "UPI-PERS-15000"
            entries.append(Entry(f"upi-{row['UPI Ref']}", "july-upi", "payment_out" if amount < 0 else "payment_in", row["Transaction Details"], abs(amount), row["Txn Date"], row["UPI Ref"], source_kind="upi_csv", description=row["Transaction Details"], personal=personal))
    result = reconcile(entries)
    exceptions = [*result.exceptions, build_exception("arithmetic_error", ("khaata-page-1",), abs(written_total - row_total))]
    order = {"unmatched_invoice": 0, "possible_duplicate": 1, "arithmetic_error": 2, "personal_vs_business": 3}
    return ReconciliationResult(result.ledger_entries, result.matches, tuple(sorted(exceptions, key=lambda x: order[x.kind])), result.unmatched_ids, store_total_paise(result.ledger_entries))
