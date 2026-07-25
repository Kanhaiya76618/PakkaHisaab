"""Strict-priority, deterministic one-to-one matching rules."""

from __future__ import annotations

from datetime import date
from difflib import SequenceMatcher

from engine.types import Entry, EntryMatch


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _days(left: Entry, right: Entry) -> int:
    return abs((_date(left.entry_date) - _date(right.entry_date)).days)


def _name(value: str | None) -> str:
    aliases = {"रमेश": "ramesh", "किराया": "rent"}
    result = (value or "").casefold().replace("ji", "").replace("bhai", "").replace("sahab", "")
    for source, target in aliases.items():
        result = result.replace(source, target)
    return " ".join(result.replace("/", " ").split())


def _compatible(left: Entry, right: Entry) -> bool:
    kinds = {left.entry_type, right.entry_type}
    return kinds in ({"purchase", "payment_out"}, {"sale", "payment_in"}, {"credit_given", "payment_out"})


def _match(left: Entry, right: Entry, rule: str, score: float) -> EntryMatch:
    return EntryMatch(left.id, right.id, rule, score)


def match_entries(left: Entry, right: Entry) -> EntryMatch | None:
    if left.upi_ref and left.upi_ref == right.upi_ref:
        return _match(left, right, "exact_ref", 1.0)
    if left.upi_ref and right.upi_ref and left.upi_ref != right.upi_ref:
        return None
    if not _compatible(left, right):
        return None
    same_amount = left.amount_paise == right.amount_paise
    same_party = _name(left.party_name) == _name(right.party_name) and bool(_name(left.party_name))
    ratio = SequenceMatcher(None, _name(left.party_name), _name(right.party_name)).ratio()
    if (left.source_kind == "voice_note" or right.source_kind == "voice_note") and same_amount and ratio >= 0.85:
        return _match(left, right, "voice_confirmed", 0.85)
    if same_amount and _days(left, right) == 0 and same_party:
        return _match(left, right, "exact_amount_date", 1.0)
    if same_amount and _days(left, right) <= 3 and same_party:
        return _match(left, right, "amount_within_window", 0.9)
    if same_amount and _days(left, right) <= 7 and ratio >= 0.85:
        return _match(left, right, "fuzzy_party_amount", 0.8)
    return None
