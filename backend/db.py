"""Small service-role store reader used exclusively by backend authorization."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from config import Settings, get_settings


@dataclass(frozen=True)
class StoreRecord:
    id: str
    owner_user_id: str | None
    is_public: bool
    is_demo: bool


class StoreRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def get_store(self, store_id: str) -> StoreRecord | None:
        """Read a store with the service role; browser requests never use this key."""
        if store_id == self.settings.demo_store_id:
            return StoreRecord(store_id, None, True, True)
        if self.settings.mock_mode or not (
            self.settings.supabase_url and self.settings.supabase_service_role_key
        ):
            return None

        headers = {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
        }
        async with httpx.AsyncClient(base_url=self.settings.supabase_url, headers=headers) as client:
            response = await client.get(
                "/rest/v1/stores",
                params={"id": f"eq.{store_id}", "select": "id,owner_user_id,is_public,is_demo"},
            )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        row = rows[0]
        return StoreRecord(
            id=row["id"],
            owner_user_id=row.get("owner_user_id"),
            is_public=bool(row["is_public"]),
            is_demo=bool(row["is_demo"]),
        )


db = StoreRepository()
