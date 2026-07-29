"""Document intake orchestration for CSV and vision extraction paths."""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Callable, Protocol

from intake.csv_parser import parse_csv_text
from intake.types import ExtractedEntryDraft
from model_router import ROUTING_TABLE, RouterError, route, route_with_fallback


KHAATA_SYSTEM_PROMPT = """You are a data-extraction engine for handwritten Indian shop ledgers (khaata).
The image may mix Hindi (Devanagari) and English, with columns like party name,
item, amount, and running totals. Extract EVERY row as JSON:
{"entries":[{"entry_type":"credit_given|payment_in|sale|note",
 "party_name":str|null,"amount_rupees":number|null,"entry_date":"YYYY-MM-DD"|null,
 "description":str,"row_ref":"page P, row N","confidence":0.0-1.0}]}
Rules: 1) NEVER invent amounts — if unreadable, amount_rupees=null and confidence<=0.3.
2) Do not sum or correct arithmetic; extract what is written, including the written total
as entry_type "note" with description "written_total". 3) Output JSON only."""

# §7.1 provides a verbatim khaata prompt but no invoice prompt. This parallel schema
# preserves the contract's no-invention and source-reference rules for invoices.
INVOICE_SYSTEM_PROMPT = """You are a data-extraction engine for Indian supplier invoices.
Extract only facts visible in the invoice as JSON:
{"entries":[{"entry_type":"purchase|sale|note","party_name":str|null,
"amount_rupees":number|null,"entry_date":"YYYY-MM-DD"|null,"description":str,
"row_ref":"page P, row N","confidence":0.0-1.0}]}
Never invent an amount or date. If a field is unreadable use null and confidence <=0.3.
Output JSON only."""


VOICE_SYSTEM_PROMPT = """You classify one spoken transaction note from an Indian shop owner.
The transcript may mix Hindi and English. Amounts in the transcript are already written as
digits - use exactly the digits present. Output JSON only:
{"entry_type":"sale|purchase|payment_in|payment_out|credit_given|credit_received|note",
"party_name":str|null,"amount_rupees":number|null,"description":str,"confidence":0.0-1.0}
Rules: 1) NEVER invent or convert an amount. If the transcript contains no digits, set
amount_rupees=null and confidence<=0.3. 2) party_name is the person or shop named, in Latin
script. 3) Output JSON only."""

# Digits only, deliberately. Saaras `transcribe` mode normalizes spoken numbers
# ("pachchees sau" -> 2500); a transcript that still spells the number out must yield no
# amount rather than a guessed one.
_AMOUNT_PATTERN = re.compile(r"(?<![\d.])\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?(?![\d])|(?<![\d.])\d+(?:\.\d{1,2})?(?![\d])")


def transcript_text(result: dict[str, Any]) -> str:
    """Read a transcript from either provider's native response shape.

    Sarvam returns `transcript`; OpenAI Whisper returns `text`. Normalizing here keeps the
    fixtures honest — each one is the shape its provider actually documents.
    """
    for key in ("transcript", "text"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise RouterError("Transcription response contained no transcript")


def amount_paise_from_transcript(transcript: str) -> int | None:
    """Largest digit amount in the transcript, as integer paise, or None."""
    if not transcript:
        return None
    best: int | None = None
    for token in _AMOUNT_PATTERN.findall(transcript):
        paise = _rupees_to_paise(token)
        if paise is not None and (best is None or paise > best):
            best = paise
    return best


@dataclass(frozen=True)
class SourceDocument:
    id: str
    store_id: str
    kind: str
    filename: str
    content: str | None = None
    audio_bytes: bytes | None = None
    audio_seconds: float = 0.0


class ExtractionRepository(Protocol):
    def add_many(self, entries: list[ExtractedEntryDraft]) -> None: ...


@dataclass
class InMemoryExtractionRepository:
    entries: list[ExtractedEntryDraft] = field(default_factory=list)

    def add_many(self, entries: list[ExtractedEntryDraft]) -> None:
        self.entries.extend(entries)


EventSink = Callable[[dict[str, str | None]], object]


def websocket_emitter(store_id: str) -> EventSink:
    """Adapt intake progress to the established store-scoped WebSocket hub."""

    async def emit(event: dict[str, str | None]) -> None:
        from events import AgentLogEvent, agent_log_hub

        await agent_log_hub.publish(store_id, AgentLogEvent(**event))

    return emit


def _rupees_to_paise(value: object) -> int | None:
    if value is None:
        return None
    try:
        rupees = Decimal(str(value).replace("₹", "").replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None
    return int((rupees * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class IntakeAgent:
    def __init__(self, *, repository: ExtractionRepository, emit: EventSink, mock_mode: bool | None = None) -> None:
        self.repository = repository
        self.emit = emit
        self.mock_mode = mock_mode

    async def _emit(self, level: str, message_en: str, message_hi: str, detail: str | None = None) -> None:
        event = {"agent": "Intake", "level": level, "message_en": message_en, "message_hi": message_hi, "detail": detail}
        result = self.emit(event)
        if inspect.isawaitable(result):
            await result

    async def process(self, document: SourceDocument) -> list[ExtractedEntryDraft]:
        await self._emit("info", f"Reading {document.filename}", f"{document.filename} पढ़ा जा रहा है", document.kind)
        if document.kind in {"bank_csv", "upi_csv"}:
            entries = parse_csv_text(document.content or "", store_id=document.store_id, source_document_id=document.id)
            self.repository.add_many(entries)
            await self._emit("success", f"Parsed {len(entries)} CSV entries", f"{len(entries)} CSV एंट्री निकाली गईं", "deterministic_parser")
            return entries

        if document.kind == "voice_note":
            return await self._process_voice_note(document)

        task_by_kind = {"khaata_photo": "vision_khaata", "invoice_image": "vision_invoice"}
        task = task_by_kind.get(document.kind)
        if task is None:
            raise RouterError(f"Unsupported intake document kind '{document.kind}'")
        await self._emit("info", f"Extracting {task.replace('_', ' ')}", "दस्तावेज़ से जानकारी निकाली जा रही है", task)
        prompt = KHAATA_SYSTEM_PROMPT if task == "vision_khaata" else INVOICE_SYSTEM_PROMPT
        payload: dict[str, Any] = {
            "source_document_id": document.id,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Extract {document.filename}."},
            ],
        }
        result = await route(task, payload, mock_mode=self.mock_mode)
        entries = self._vision_entries(document, task, result)
        self.repository.add_many(entries)
        await self._emit("success", f"Extracted {len(entries)} entries from {document.filename}", f"{document.filename} से {len(entries)} एंट्री निकाली गईं", task)
        return entries

    async def _process_voice_note(self, document: SourceDocument) -> list[ExtractedEntryDraft]:
        """Transcribe Indic-first, then classify. The provider that served is logged."""
        await self._emit(
            "info", "Transcribing with Sarvam Saaras v3",
            "Sarvam Saaras v3 से लिप्यंतरण हो रहा है", "transcribe_indic",
        )
        payload: dict[str, Any] = {
            "audio_bytes": document.audio_bytes,
            "filename": document.filename,
            "audio_seconds": document.audio_seconds,
        }
        transcription, provenance = await route_with_fallback(
            "transcribe_indic", payload, mock_mode=self.mock_mode
        )
        transcript = transcript_text(transcription)
        if provenance.fell_back_from:
            await self._emit(
                "warning",
                f"Sarvam unavailable — transcribed with {provenance.model} instead",
                f"Sarvam उपलब्ध नहीं — {provenance.model} से लिप्यंतरण किया गया",
                f"{provenance.provider}:{provenance.model} fallback_from={provenance.fell_back_from}",
            )
        else:
            await self._emit(
                "success", f"Transcribed by {provenance.model}",
                f"{provenance.model} ने लिप्यंतरण किया", f"{provenance.provider}:{provenance.model}",
            )

        classification = await route(
            "classify_txn",
            {
                "messages": [
                    {"role": "system", "content": VOICE_SYSTEM_PROMPT},
                    {"role": "user", "content": transcript},
                ]
            },
            mock_mode=self.mock_mode,
        )
        # The model may name the party and the type; the amount is taken from the
        # transcript digits so no model can introduce a figure that was never spoken.
        amount_paise = amount_paise_from_transcript(transcript)
        model_amount = _rupees_to_paise(classification.get("amount_rupees"))
        if amount_paise is None:
            amount_paise = model_amount
        confidence = classification.get("confidence", 0.0)
        entry = ExtractedEntryDraft(
            store_id=document.store_id,
            source_document_id=document.id,
            entry_type=str(classification.get("entry_type") or "note"),
            party_name=classification.get("party_name") if isinstance(classification.get("party_name"), str) else None,
            amount_paise=amount_paise,
            entry_date=None,
            description=transcript,
            confidence=confidence if isinstance(confidence, float) else 0.0,
            extraction_model=f"{provenance.model}+{ROUTING_TABLE['classify_txn'].model}",
            bbox_or_line_ref="voice note, full transcript",
        )
        self.repository.add_many([entry])
        await self._emit(
            "success", f"Voice note became 1 entry ({transcript[:40]})",
            f"वॉइस नोट से 1 एंट्री बनी ({transcript[:40]})", "classify_txn",
        )
        return [entry]

    def _vision_entries(self, document: SourceDocument, task: str, result: dict[str, Any]) -> list[ExtractedEntryDraft]:
        raw_entries = result.get("entries")
        if not isinstance(raw_entries, list):
            raise RouterError("Vision response does not contain an entries array")
        entries: list[ExtractedEntryDraft] = []
        for index, raw in enumerate(raw_entries, start=1):
            if not isinstance(raw, dict):
                continue
            amount_paise = _rupees_to_paise(raw.get("amount_rupees"))
            confidence = raw.get("confidence", 0.0)
            if not isinstance(confidence, float):
                confidence = 0.0
            entries.append(
                ExtractedEntryDraft(
                    store_id=document.store_id,
                    source_document_id=document.id,
                    entry_type=str(raw.get("entry_type") or "note"),
                    party_name=raw.get("party_name") if isinstance(raw.get("party_name"), str) else None,
                    amount_paise=amount_paise,
                    entry_date=raw.get("entry_date") if isinstance(raw.get("entry_date"), str) else None,
                    description=str(raw.get("description") or ""),
                    confidence=confidence,
                    extraction_model=ROUTING_TABLE[task].model,
                    bbox_or_line_ref=str(raw.get("row_ref") or f"row {index}"),
                )
            )
        return entries
