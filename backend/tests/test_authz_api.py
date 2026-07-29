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


def test_cors_admits_vercel_origins_without_chasing_preview_urls() -> None:
    """Vercel mints a new hostname for every preview deploy, so pinning one exact origin in
    FRONTEND_ORIGIN breaks each new deployment. A missing allow-origin header makes the
    browser discard an otherwise-successful 200, which surfaces as "could not load"."""
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as fresh:
        for origin in (
            "https://pakkahisaab.vercel.app",
            "https://pakkahisaab-git-main-kanhaiya.vercel.app",
            "http://localhost:3000",
        ):
            response = fresh.get("/api/health", headers={"Origin": origin})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == origin, origin


def test_cors_still_refuses_an_unrelated_origin() -> None:
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as fresh:
        response = fresh.get("/api/health", headers={"Origin": "https://evil.example.com"})
        assert "access-control-allow-origin" not in response.headers
