from __future__ import annotations

from pathlib import Path

from second_brain.core.settings import Settings


def test_settings_defaults_are_project_shaped() -> None:
    settings = Settings()

    assert settings.vault_path == Path("/Volumes/VeN/Claude-Code-Work/Brain")
    assert settings.chroma_path == Path("state/chroma")
    assert settings.prompts_root == Path("/Volumes/VeN/Claude-Code-Work/prompts")
    assert settings.embedding_model == "google/embeddinggemma-300m"
    assert settings.fallback_embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.embedding_truncate_dim is None
    assert settings.schedule_time == "07:00"
    assert settings.freshness_days == 7


def test_settings_accept_runtime_overrides(tmp_path: Path) -> None:
    settings = Settings(
        vault_path=tmp_path / "vault",
        db_path=tmp_path / "state" / "sbo.db",
        anthropic_api_key="test-key",
    )

    assert settings.vault_path == tmp_path / "vault"
    assert settings.db_path == tmp_path / "state" / "sbo.db"
    assert settings.anthropic_api_key == "test-key"
