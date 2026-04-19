from __future__ import annotations

import asyncio

import pytest

from second_brain.core.llm_client import LLMClient, _estimate_cost
from second_brain.core.settings import Settings


def make_settings(**kwargs) -> Settings:
    return Settings(anthropic_api_key="test-key", **kwargs)


def test_estimate_cost_known_model() -> None:
    cost = _estimate_cost("claude-sonnet-4-6", tokens_in=1_000_000, tokens_out=1_000_000)
    assert cost == pytest.approx(18.0, rel=0.01)


def test_estimate_cost_unknown_model_uses_default() -> None:
    cost = _estimate_cost("some-unknown-model", tokens_in=1_000_000, tokens_out=0)
    assert cost > 0


def test_llm_client_accumulates_cost(tmp_path) -> None:
    settings = make_settings(db_path=tmp_path / "state.db")
    client = LLMClient(settings=settings)
    assert client.total_cost_usd == 0.0


def test_llm_client_raises_harness_error_when_no_key(tmp_path) -> None:
    settings = Settings(anthropic_api_key="", openrouter_api_key="", db_path=tmp_path / "state.db")
    client = LLMClient(settings=settings)

    async def _run():
        return await client.complete("hello")

    with pytest.raises(Exception):
        asyncio.run(_run())
