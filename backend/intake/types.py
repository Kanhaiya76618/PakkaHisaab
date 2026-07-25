"""Typed immutable extraction drafts shared by every intake path."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedEntryDraft:
    store_id: str
    source_document_id: str
    entry_type: str
    party_name: str | None
    amount_paise: int | None
    entry_date: str | None
    description: str
    confidence: float
    extraction_model: str
    bbox_or_line_ref: str | None
    upi_ref: str | None = None
