from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from .config import get_settings


@lru_cache
def _build_supabase_client() -> Client:
    settings = get_settings()
    return create_client(str(settings.supabase_url), settings.supabase_service_role_key)


def get_service_client() -> Client:
    """Return Supabase client that uses the service role key."""

    return _build_supabase_client()


def get_anon_client() -> Optional[Client]:
    """Return Supabase client built with anon key for limited operations."""

    settings = get_settings()
    if not settings.supabase_anon_key:
        return None
    return create_client(str(settings.supabase_url), settings.supabase_anon_key)
