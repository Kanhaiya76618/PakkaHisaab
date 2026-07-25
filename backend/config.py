"""Runtime configuration. Values are supplied by environment variables only."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEMO_STORE_ID = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    mock_mode: bool = os.getenv("MOCK_MODE", "false").lower() == "true"
    demo_store_id: str = os.getenv("DEMO_STORE_ID", DEMO_STORE_ID)
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")


def get_settings() -> Settings:
    return Settings()
