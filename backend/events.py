"""In-memory structured agent-log stream for the Day 1 WebSocket contract."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from fastapi import WebSocket
from pydantic import BaseModel


class AgentLogEvent(BaseModel):
    agent: str
    level: Literal["info", "success", "warning", "error"]
    message_en: str
    message_hi: str
    detail: str | None = None


INITIAL_EVENT = AgentLogEvent(
    agent="System",
    level="info",
    message_en="Agent log connected. Demo replay is ready.",
    message_hi="एजेंट लॉग जुड़ गया। डेमो रीप्ले तैयार है।",
    detail="mock_mode_safe_connection",
)


class AgentLogHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, store_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[store_id].add(websocket)
        await websocket.send_json(INITIAL_EVENT.model_dump())

    def disconnect(self, store_id: str, websocket: WebSocket) -> None:
        self._connections[store_id].discard(websocket)
        if not self._connections[store_id]:
            self._connections.pop(store_id, None)

    async def publish(self, store_id: str, event: AgentLogEvent) -> None:
        for websocket in list(self._connections.get(store_id, set())):
            await websocket.send_json(event.model_dump())


agent_log_hub = AgentLogHub()
