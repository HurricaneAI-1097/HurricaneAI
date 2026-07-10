"""Application configuration using Pydantic BaseSettings.

All configuration values are sourced from environment variables (or a local
.env file during development). A cached singleton accessor `get_settings()`
is exposed so the settings object is only constructed once per process.

Secrets (DATABASE_URL, SUPABASE_*, OPENAI_API_KEY) default to empty strings
so the server can boot even before secrets are injected — actual API calls
will fail with 500/503 if they're still missing at request time.
"""

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App -----------------------------------------------------------
    APP_NAME: str = "HurricaneAI Lead Generation API"
    APP_ENV: Literal["dev", "staging", "prod"] = "dev"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Database -------------------------------------------------------
    # Default to empty so container boots before secrets are injected.
    # Prisma / routes will fail gracefully rather than crashing on startup.
    DATABASE_URL: str = Field(
        default="",
        description="PostgreSQL connection string (Supabase pooler, port 6543)",
    )

    # --- Supabase -------------------------------------------------------
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_KEY: str = Field(
        default="", description="Supabase service_role or anon key"
    )
    SUPABASE_JWT_SECRET: str = Field(
        default="",
        description="Secret used to verify Supabase-issued JWTs (min 32 chars)",
    )

    # --- OpenAI / LangChain ---------------------------------------------
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.2

    # --- Redis / ARQ ----------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- CORS -----------------------------------------------------------
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://hurricaneai.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # --- Pagination -----------------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # --- Derived helpers ------------------------------------------------
    @property
    def db_configured(self) -> bool:
        return bool(self.DATABASE_URL)

    @property
    def supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_KEY and self.SUPABASE_JWT_SECRET)

    @property
    def openai_configured(self) -> bool:
        return bool(self.OPENAI_API_KEY)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton per process)."""
    return Settings()
