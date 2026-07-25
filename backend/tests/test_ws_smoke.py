from fastapi.testclient import TestClient

from main import DEMO_STORE_ID, app


def test_agent_log_websocket_streams_a_structured_event() -> None:
    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/stores/{DEMO_STORE_ID}/agent-log") as ws:
            event = ws.receive_json()

    assert set(event) == {"agent", "level", "message_en", "message_hi", "detail"}
    assert event["agent"] == "System"
    assert event["level"] == "info"
    assert event["message_en"]
    assert event["message_hi"]
