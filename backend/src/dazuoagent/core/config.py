"""Application settings loaded from environment / .env.

Single source of truth — every other module imports `settings` from here,
never reads `os.environ` directly. Add new knobs by extending `Settings` and
adding them to `.env.example`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Repo path layout: backend/src/dazuoagent/core/config.py
#   parents[0] = core/
#   parents[1] = dazuoagent/
#   parents[2] = src/
#   parents[3] = backend/         ← where .env lives
#   parents[4] = repo root        ← where data/, frontend/, etc. live
_REPO_ROOT = Path(__file__).resolve().parents[4]
_BACKEND_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Typed runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
        ],
    )
    environment: Literal["dev", "test", "prod"] = "dev"

    # --- Database ---
    # SQLite default for now. Switch to postgresql+psycopg://... in prod.
    database_url: str = f"sqlite:///{(_REPO_ROOT / 'data' / 'db' / 'dazuoagent.sqlite').as_posix()}"
    database_echo: bool = False

    # --- LLM Agent ---
    # Each provider has its own (key, model, optional base_url) triple. The
    # active provider is selected via `llm_provider`.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"

    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    llm_provider: Literal["openai", "anthropic", "deepseek", "mock"] = "mock"

    # --- File uploads ---
    upload_dir: Path = _REPO_ROOT / "data" / "uploads"
    max_upload_bytes: int = 20 * 1024 * 1024  # 20 MB


settings = Settings()
