from __future__ import annotations

import pytest

from second_brain.research.ask import AskService, AskResult
from second_brain.vault.index import SearchResult


class FakeVaultIndex:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.queries: list[tuple[str, int]] = []

    def search(self, query: str, limit: int = 5, project: str | None = None) -> list[SearchResult]:
        self.queries.append((query, limit))
        return self.results


class FakeLLMClient:
    def __init__(self) -> None:
        self.prompts: list[dict[str, str | int]] = []

    async def complete(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 2048,
    ):
        self.prompts.append({"prompt": prompt, "system": system, "max_tokens": max_tokens})
        return AskResult(
            answer="Context engineering allocates scarce tokens to the most useful evidence.",
            sources=["Brain/note.md"],
            cost_usd=0.01,
            tokens_used=42,
        )


@pytest.mark.asyncio
async def test_ask_service_synthesizes_answer_from_vault_evidence() -> None:
    evidence = [
        SearchResult(
            text="Token budgets should favor task instructions and high-relevance evidence.",
            path="Brain/note.md",
            title="Context Engineering",
            heading="Budgeting",
            score=0.91,
            chunk_index=0,
        )
    ]
    llm = FakeLLMClient()
    service = AskService(vault_index=FakeVaultIndex(evidence), llm_client=llm)

    result = await service.ask("what is context engineering?", limit=3)

    assert result.answer.startswith("Context engineering")
    assert result.sources == ["Brain/note.md"]
    assert "Token budgets should favor" in str(llm.prompts[0]["prompt"])
    assert "what is context engineering?" in str(llm.prompts[0]["prompt"])


@pytest.mark.asyncio
async def test_ask_service_returns_no_evidence_message_without_llm_call() -> None:
    llm = FakeLLMClient()
    service = AskService(vault_index=FakeVaultIndex([]), llm_client=llm)

    result = await service.ask("unknown topic")

    assert result.answer == "No relevant vault notes found."
    assert result.sources == []
    assert llm.prompts == []
