from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


class SentenceTransformerLike(Protocol):
    def encode(
        self,
        texts: list[str],
        **kwargs: object,
    ) -> list[list[float]]:
        ...


@dataclass
class EmbeddingProvider:
    model_name: str = "google/embeddinggemma-300m"
    fallback_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    truncate_dim: int | None = None
    model: SentenceTransformerLike | None = None
    model_factory: Callable[..., SentenceTransformerLike] | None = None

    def __post_init__(self) -> None:
        if self.model is None:
            self.model = self._load_model()

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text], prompt_name="Retrieval-query")[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._encode(texts, prompt_name="Retrieval-document")

    def _encode(self, texts: list[str], prompt_name: str) -> list[list[float]]:
        if self.model is None:
            raise RuntimeError("Embedding model was not initialized")
        kwargs: dict[str, object] = {"normalize_embeddings": True}
        if self._supports_prompt(prompt_name):
            kwargs["prompt_name"] = prompt_name
        vectors = self.model.encode(texts, **kwargs)
        return [[float(value) for value in vector] for vector in vectors]

    def _load_model(self) -> SentenceTransformerLike:
        factory = self.model_factory
        if factory is None:
            from sentence_transformers import SentenceTransformer

            factory = SentenceTransformer

        kwargs = {}
        if self.truncate_dim is not None:
            kwargs["truncate_dim"] = self.truncate_dim
        try:
            return factory(self.model_name, **kwargs)
        except (OSError, RuntimeError):
            return factory(self.fallback_model_name, **kwargs)

    def _supports_prompt(self, prompt_name: str) -> bool:
        prompts = getattr(self.model, "prompts", None)
        if isinstance(prompts, dict):
            return prompt_name in prompts
        return True
