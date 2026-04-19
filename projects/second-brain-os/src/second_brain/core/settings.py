from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    github_token: str = ""

    vault_path: Path = Path("/Volumes/VeN/Claude-Code-Work/Brain")
    db_path: Path = Path("state/sbo.db")
    chroma_path: Path = Path("state/chroma")
    prompts_root: Path = Path("/Volumes/VeN/Claude-Code-Work/prompts")
    embedding_model: str = "google/embeddinggemma-300m"
    fallback_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_truncate_dim: int | None = None

    schedule_time: str = "07:00"
    default_model: str = "claude-sonnet-4-6"
    fallback_model: str = "anthropic/claude-sonnet-4-6"
    max_tokens_per_call: int = 8000
    freshness_days: int = 7
    log_level: str = "INFO"
