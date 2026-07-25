"""Storage path and URL rules shared by upload and Evidence Passport flows."""

from __future__ import annotations

from pathlib import PurePosixPath


def document_storage_path(bucket: str, store_id: str, document_id: str, filename: str) -> str:
    """Return the object key; bucket selection is kept separate for Supabase APIs."""
    suffix = PurePosixPath(filename).suffix.lower()
    return f"{store_id}/{document_id}{suffix}"


def get_document_url(
    bucket: str,
    path: str,
    *,
    supabase_url: str | None = None,
    signed_url: str | None = None,
) -> str:
    if bucket == "user-uploads":
        if not signed_url:
            raise ValueError("private documents require a signed URL")
        return signed_url
    if bucket != "demo-assets" or not supabase_url:
        raise ValueError("public demo documents require a Supabase URL")
    return f"{supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{path}"
