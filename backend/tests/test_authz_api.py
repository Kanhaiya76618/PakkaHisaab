from fastapi.testclient import TestClient

from auth import ensure_authorized_store
from db import StoreRecord
from main import DEMO_STORE_ID, app


client = TestClient(app)


def test_health_reports_ready() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_anonymous_demo_store_is_available() -> None:
    response = client.post("/api/stores/demo")

    assert response.status_code == 200
    assert response.json()["store_id"] == DEMO_STORE_ID
    assert response.json()["is_public"] is True


def test_upload_contract_exists_for_the_public_demo() -> None:
    response = client.post(
        f"/api/stores/{DEMO_STORE_ID}/uploads",
        data={"kind": "upi_csv"},
        files={"file": ("july.csv", "Amount,Txn Date\n10,2026-07-01\n", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["document_id"]
    assert response.json()["entry_count"] == 1


def test_anonymous_request_cannot_access_private_ownerless_store(monkeypatch) -> None:
    async def private_ownerless_store(_: str) -> StoreRecord:
        return StoreRecord("private-store", None, False, False)

    monkeypatch.setattr("auth.db.get_store", private_ownerless_store)

    from fastapi import HTTPException
    import asyncio

    try:
        asyncio.run(ensure_authorized_store("private-store", None))
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("anonymous caller received a private ownerless store")
