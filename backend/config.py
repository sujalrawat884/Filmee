from functools import lru_cache
from pathlib import Path

from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration pulled from environment variables."""

    supabase_url: HttpUrl
    supabase_anon_key: str
    supabase_service_role_key: str

    class Config:
        env_file = Path(__file__).resolve().parent / ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
