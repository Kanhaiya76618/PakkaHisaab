"""Day 1 FastAPI entry point for PakkaHisaab."""

from __future__ import annotations

from contextlib import suppress
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from auth import current_user, ensure_authorized_store
from config import DEMO_STORE_ID, get_settings
from events import agent_log_hub
from agents.intake_agent import InMemoryExtractionRepository, IntakeAgent, SourceDocument, websocket_emitter


app = FastAPI(title="PakkaHisaab API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_repository = InMemoryExtractionRepository()


@app.get("/api/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {"status": "ok", "service": "pakkahisaab-api", "mock_mode": settings.mock_mode}


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
