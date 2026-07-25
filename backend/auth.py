"""Supabase JWT verification and store-scoped authorization."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWTError

from config import get_settings
from db import StoreRecord, db


async def current_user(authorization: str | None = Header(None)) -> str | None:
    """Returns user_id, or None for anonymous callers (demo store access)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(
            authorization[7:],
            get_settings().supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload["sub"]
    except PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired session") from exc


async def ensure_authorized_store(store_id: str, user_id: str | None) -> StoreRecord:
    store = await db.get_store(store_id)  # service-role read, then explicit API gate
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    if store.is_public or (user_id is not None and store.owner_user_id == user_id):
        return store
    raise HTTPException(status_code=403, detail="You do not have access to this store")


async def authorize_store(
    store_id: str, user_id: Annotated[str | None, Depends(current_user)]
) -> StoreRecord:
    return await ensure_authorized_store(store_id, user_id)
