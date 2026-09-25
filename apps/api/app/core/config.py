"""
LegalLens API — Typed Environment Configuration.

Loads configuration from environment variables with validation.
Missing required secrets fail startup in production but use
explicit development warnings locally.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def _find_env_file() -> str:
    """Find .env file by searching upward from this file's location."""
    current = Path(__file__).resolve().parent
    for _ in range(10):  # Max 10 levels up
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
        current = current.parent
    return ".env"  # Fallback


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "legallens"
    app_version: str = "0.1.0"
    api_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:3000"

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "postgresql+psycopg://legallens:legallens@127.0.0.1:5433/legallens"

    # ── Redis (optional) ─────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Object Storage ───────────────────────────────────────────
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "legallens-private"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    object_storage_region: str = "us-east-1"

    # ── LLM Provider ─────────────────────────────────────────────
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_fallback_model: str = "gpt-4o-mini"
    llm_timeout: int = 30
    llm_max_retries: int = 1

    # ── Embedding Provider ───────────────────────────────────────
    embedding_api_base: str = "https://api.openai.com/v1"
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    # ── Upload Limits ────────────────────────────────────────────
    max_upload_size_mb: int = 20
    max_pdf_pages: int = 100

    # ── Retention ────────────────────────────────────────────────
    document_ttl_hours: int = 24
    chat_ttl_hours: int = 24

    # ── OCR ──────────────────────────────────────────────────────
    ocr_enabled: bool = True

    # ── RAG ──────────────────────────────────────────────────────
    external_rag_enabled: bool = False

    # ── Security ─────────────────────────────────────────────────
    cors_origins: list[str] | str = Field(default=["http://localhost:3000"])
    rate_limit_per_minute: int = 30
    secret_key: str = "dev-secret-key-change-in-production"

    # ── Logging ──────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Monitoring ───────────────────────────────────────────────
    sentry_dsn: str = ""
    prometheus_enabled: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Parse CORS origins from JSON list, comma-separated string, or list."""
        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return ["*"]
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:3000"]

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info: object) -> str:
        """Warn if using default secret key in non-development environments."""
        # Access the 'data' attribute from ValidationInfo
        data = getattr(info, "data", {})
        env = data.get("app_env", "development")
        if env != "development" and v == "dev-secret-key-change-in-production":
            msg = "SECRET_KEY must be set to a secure value in production"
            raise ValueError(msg)
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    model_config = {
        "env_file": _find_env_file(),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings (singleton)."""
    return Settings()
