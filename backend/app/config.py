"""Application configuration using Pydantic BaseSettings.

All configuration values are sourced from environment variables (or a local
.env file during development). A cached singleton accessor `get_settings()`
is exposed so the settings object is only constructed once per process.
"""

from functools import lru_cache
from typing import List, Literal

from pydantic import AnyHttpUrl, Field, field_validator
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
    APP_NAME: str = "AI Lead Generation API"
    APP_ENV: Literal["dev", "staging", "prod"] = "dev"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Database --------------------------------------------------------
    DATABASE_URL: str = Field(
        ..., description="PostgreSQL connection string (Supabase)"
    )

    # --- Supabase --------------------------------------------------------
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_KEY: str = Field(..., description="Supabase service role / anon key")
    SUPABASE_JWT_SECRET: str = Field(
        ..., description="Secret used to verify Supabase-issued JWTs"
    )

    # --- OpenAI / LangChain ----------------------------------------------
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.2

    # --- Redis / ARQ -------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- CORS --------------------------------------------------------------
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # --- Pagination ----------------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton per process)."""
    return Settings()
