"""Day 1 FastAPI entry point for PakkaHisaab."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from auth import current_user, ensure_authorized_store
from config import DEMO_STORE_ID, get_settings
from events import agent_log_hub
from agents.intake_agent import InMemoryExtractionRepository, IntakeAgent, SourceDocument, websocket_emitter
from engine.reconciler import reconcile_sample_data
from events import AgentLogEvent
from evals.runner import run as run_evals


app = FastAPI(title="PakkaHisaab API", version="0.1.0")
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_repository = InMemoryExtractionRepository()
reconciliation_state: dict[str, dict[str, object]] = {}
ROOT = Path(__file__).resolve().parents[1]
VALID_RESOLUTION_ACTIONS = {"create_entry", "merge_duplicates", "mark_personal", "adjust_amount", "ask_user"}


class ResolveRequest(BaseModel):
    action: str


async def _stage(store_id: str, agent: str, message_en: str, message_hi: str) -> None:
    await agent_log_hub.publish(store_id, AgentLogEvent(agent=agent, level="info", message_en=message_en, message_hi=message_hi, detail="live"))


@app.get("/api/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {"status": "ok", "service": "pakkahisaab-api", "mock_mode": settings.mock_mode}


@app.get("/api/evals/run")
async def evals_run() -> dict[str, object]:
    return run_evals()


@app.post("/api/stores/demo")
async def demo_store() -> dict[str, object]:
    """Anonymous entry point for the public, seeded demo store."""
    return {"store_id": get_settings().demo_store_id, "is_public": True, "is_demo": True}


@app.post("/api/stores/{store_id}/uploads")
async def upload_document(
    store_id: str,
    kind: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, object]:
    await ensure_authorized_store(store_id, None)
    document_id = str(uuid4())
    content = (await file.read()).decode("utf-8", errors="replace") if kind in {"bank_csv", "upi_csv"} else None
    document = SourceDocument(document_id, store_id, kind, file.filename or "upload", content)
    entries = await IntakeAgent(
        repository=upload_repository,
        emit=websocket_emitter(store_id),
        mock_mode=get_settings().mock_mode,
    ).process(document)
    return {"document_id": document_id, "entry_count": len(entries)}


@app.post("/api/stores/{store_id}/reconcile")
async def reconcile_store(store_id: str) -> dict[str, object]:
    await ensure_authorized_store(store_id, None)
    await _stage(store_id, "Reconciler", "Running deterministic reconciliation", "निर्धारित मिलान चल रहा है")
    result = reconcile_sample_data(ROOT / "sample_data")
    await _stage(store_id, "Exception", "Detecting exceptions", "अपवाद खोजे जा रहे हैं")
    exceptions = [{"id": f"exception-{index}", **asdict(item), "status": "open"} for index, item in enumerate(result.exceptions, 1)]
    reconciliation_state[store_id] = {"result": result, "exceptions": exceptions}
    await _stage(store_id, "Audit", "Evidence audit complete", "साक्ष्य ऑडिट पूरा हुआ")
    return {"ledger_total_paise": result.ledger_total_paise, "exception_count": len(exceptions), "match_count": len(result.matches)}


@app.post("/api/demo/reset")
async def reset_demo() -> dict[str, object]:
    """Reset the public demo on demand; works when pg_cron is unavailable."""
    store_id = get_settings().demo_store_id
    result = reconcile_sample_data(ROOT / "sample_data")
    reconciliation_state[store_id] = {
        "result": result,
        "exceptions": [{"id": f"exception-{index}", **asdict(item), "status": "open"} for index, item in enumerate(result.exceptions, 1)],
    }
    await _stage(store_id, "System", "Demo data reset", "डेमो डेटा रीसेट हुआ")
    return {"store_id": store_id, "reset": True, "exception_count": 4}


@app.get("/api/stores/{store_id}/ledger")
async def ledger(store_id: str) -> dict[str, object]:
    await ensure_authorized_store(store_id, None)
    state = reconciliation_state.get(store_id)
    if not state:
        raise HTTPException(409, "Run reconciliation first")
    result = state["result"]
    return {"entries": [asdict(item) for item in result.ledger_entries], "total_paise": result.ledger_total_paise}


@app.get("/api/stores/{store_id}/exceptions")
async def exceptions(store_id: str) -> dict[str, object]:
    await ensure_authorized_store(store_id, None)
    state = reconciliation_state.get(store_id)
    return {"exceptions": [] if not state else state["exceptions"]}


@app.post("/api/exceptions/{exception_id}/resolve")
async def resolve_exception(exception_id: str, body: ResolveRequest) -> dict[str, object]:
    if body.action not in VALID_RESOLUTION_ACTIONS:
        raise HTTPException(422, "Invalid resolution action")
    for state in reconciliation_state.values():
        for item in state["exceptions"]:
            if item["id"] == exception_id:
                item["status"] = "resolved"
                item["resolution"] = body.action
                return item
    raise HTTPException(404, "Exception not found")


@app.get("/api/ledger-entries/{ledger_entry_id}/evidence")
async def ledger_evidence(ledger_entry_id: str) -> dict[str, object]:
    for store_id, state in reconciliation_state.items():
        result = state["result"]
        entry = next((item for item in result.ledger_entries if item.id == ledger_entry_id), None)
        if not entry:
            continue
        await ensure_authorized_store(store_id, None)
        linked = [asdict(match) for match in result.matches if ledger_entry_id in {match.left_id, match.right_id}]
        return {"ledger_entry_id": ledger_entry_id, "store_id": store_id, "sources": [{"source_id": entry.source_id, "entry_id": entry.id, "entry_type": entry.entry_type}], "matches": linked}
    raise HTTPException(404, "Ledger entry not found")


@app.websocket("/ws/stores/{store_id}/agent-log")
async def stream_agent_log(websocket: WebSocket, store_id: str) -> None:
    try:
        user_id = await current_user(websocket.headers.get("authorization"))
        await ensure_authorized_store(store_id, user_id)
    except HTTPException as exc:
        await websocket.close(code=4404 if exc.status_code == 404 else 4403)
        return

    await agent_log_hub.connect(store_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        with suppress(KeyError):
            agent_log_hub.disconnect(store_id, websocket)


__all__ = ["app", "DEMO_STORE_ID"]
