from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    id: str
    source_id: str
    entry_type: str
    party_name: str | None
    amount_paise: int
    entry_date: str
    upi_ref: str | None = None
    source_kind: str = ""
    description: str = ""
    personal: bool = False


@dataclass(frozen=True)
class EntryMatch:
    left_id: str
    right_id: str
    match_rule: str
    match_score: float


@dataclass(frozen=True)
class ExceptionRecord:
    kind: str
    related_entry_ids: tuple[str, ...]
    amount_paise: int = 0
    summary_en: str = ""
    summary_hi: str = ""
    suggested_action: str = "ask_user"
    party_name: str | None = None


@dataclass(frozen=True)
class ReconciliationResult:
    ledger_entries: tuple[Entry, ...]
    matches: tuple[EntryMatch, ...]
    exceptions: tuple[ExceptionRecord, ...]
    unmatched_ids: tuple[str, ...]
    ledger_total_paise: int
