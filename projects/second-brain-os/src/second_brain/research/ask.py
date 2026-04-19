from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from second_brain.core.llm_client import LLMClient
from second_brain.core.settings import Settings
from second_brain.vault.index import SearchResult, VaultIndex


class VaultIndexLike(Protocol):
    def search(self, query: str, limit: int = 5, project: str | None = None) -> list[SearchResult]:
        ...


class LLMClientLike(Protocol):
    async def complete(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 2048,
    ):
        ...


@dataclass
class AskResult:
    answer: str
    sources: list[str]
    cost_usd: float = 0.0
    tokens_used: int = 0


@dataclass
class AskService:
    vault_index: VaultIndexLike
    llm_client: LLMClientLike

    @classmethod
    def from_settings(cls, settings: Settings) -> "AskService":
        return cls(
            vault_index=VaultIndex.from_settings(settings),
            llm_client=LLMClient(settings),
        )

    async def ask(self, question: str, limit: int = 5) -> AskResult:
        evidence = self.vault_index.search(question, limit=limit)
        if not evidence:
            return AskResult(answer="No relevant vault notes found.", sources=[])

        prompt = self._build_prompt(question, evidence)
        response = await self.llm_client.complete(
            prompt=prompt,
            system=(
                "You answer from the user's Obsidian vault evidence. "
                "Use only the supplied evidence, cite source paths, and say when evidence is incomplete."
            ),
            max_tokens=1200,
        )
        if isinstance(response, AskResult):
            return response

        sources = self._sources_from(evidence)
        return AskResult(
            answer=response.content,
            sources=sources,
            cost_usd=response.cost_usd,
            tokens_used=response.tokens_in + response.tokens_out,
        )

    def _build_prompt(self, question: str, evidence: list[SearchResult]) -> str:
        evidence_blocks = []
        for index, result in enumerate(evidence, start=1):
            evidence_blocks.append(
                "\n".join(
                    [
                        f"[{index}] {result.title} > {result.heading}",
                        f"Path: {result.path}",
                        f"Score: {result.score:.2f}",
                        result.text,
                    ]
                )
            )
        return "\n\n".join(
            [
                f"Question: {question}",
                "Vault evidence:",
                "\n\n".join(evidence_blocks),
                "Answer with concise synthesis and a Sources section.",
            ]
        )

    def _sources_from(self, evidence: list[SearchResult]) -> list[str]:
        sources: list[str] = []
        for result in evidence:
            if result.path and result.path not in sources:
                sources.append(result.path)
        return sources
