import os
from functools import lru_cache

from app.config import load_environment

try:
    from supabase import Client, create_client
except Exception:  # pragma: no cover - local fallback mode
    Client = object
    create_client = None


@lru_cache
def get_supabase() -> Client | None:
    load_environment()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key or create_client is None:
        return None
    return create_client(url, key)
