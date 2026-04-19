from __future__ import annotations

import numpy as np

from second_brain.embeddings.provider import EmbeddingProvider


class FakeSentenceTransformer:
    def __init__(self, model_name: str, truncate_dim: int | None = None) -> None:
        self.model_name = model_name
        self.truncate_dim = truncate_dim
        self.calls: list[dict[str, object]] = []

    def encode(
        self,
        texts: list[str],
        *,
        prompt_name: str,
        normalize_embeddings: bool,
    ) -> list[list[float]]:
        self.calls.append(
            {
                "texts": texts,
                "prompt_name": prompt_name,
                "normalize_embeddings": normalize_embeddings,
            }
        )
        width = self.truncate_dim or 3
        return [[float(index + offset) for offset in range(width)] for index, _ in enumerate(texts)]


class FakeModelWithoutPrompts:
    prompts: dict[str, str] = {}

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def encode(self, texts: list[str], **kwargs) -> list[list[float]]:  # type: ignore[no-untyped-def]
        self.calls.append({"texts": texts, **kwargs})
        return [[1.0, 2.0, 3.0] for _ in texts]


class FakeNumpyModel:
    def encode(self, texts: list[str], **kwargs):  # type: ignore[no-untyped-def]
        return [[np.float32(0.25), np.float32(0.5)] for _ in texts]


def test_embedding_provider_uses_retrieval_prompts() -> None:
    fake_model = FakeSentenceTransformer("google/embeddinggemma-300m", truncate_dim=3)
    provider = EmbeddingProvider(model=fake_model, model_name="google/embeddinggemma-300m")

    query_vector = provider.embed_query("context window engineering")
    document_vectors = provider.embed_documents(["# ContextForge\nToken budgets matter."])

    assert query_vector == [0.0, 1.0, 2.0]
    assert document_vectors == [[0.0, 1.0, 2.0]]
    assert fake_model.calls[0]["prompt_name"] == "Retrieval-query"
    assert fake_model.calls[1]["prompt_name"] == "Retrieval-document"
    assert fake_model.calls[0]["normalize_embeddings"] is True


def test_embedding_provider_batches_documents() -> None:
    fake_model = FakeSentenceTransformer("google/embeddinggemma-300m", truncate_dim=2)
    provider = EmbeddingProvider(model=fake_model, model_name="google/embeddinggemma-300m")

    vectors = provider.embed_documents(["alpha", "beta"])

    assert vectors == [[0.0, 1.0], [1.0, 2.0]]
    assert fake_model.calls[0]["texts"] == ["alpha", "beta"]


def test_embedding_provider_falls_back_when_primary_model_is_gated() -> None:
    loaded: list[str] = []
    fallback = FakeModelWithoutPrompts()

    def model_factory(model_name: str, **kwargs):  # type: ignore[no-untyped-def]
        loaded.append(model_name)
        if model_name == "google/embeddinggemma-300m":
            raise OSError("gated repo")
        return fallback

    provider = EmbeddingProvider(
        model_name="google/embeddinggemma-300m",
        fallback_model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_factory=model_factory,
    )

    vector = provider.embed_query("context engineering")

    assert loaded == ["google/embeddinggemma-300m", "sentence-transformers/all-MiniLM-L6-v2"]
    assert vector == [1.0, 2.0, 3.0]
    assert "prompt_name" not in fallback.calls[0]


def test_embedding_provider_falls_back_when_primary_model_metadata_check_fails() -> None:
    loaded: list[str] = []
    fallback = FakeModelWithoutPrompts()

    def model_factory(model_name: str, **kwargs):  # type: ignore[no-untyped-def]
        loaded.append(model_name)
        if model_name == "google/embeddinggemma-300m":
            raise RuntimeError("Cannot send a request, as the client has been closed.")
        return fallback

    provider = EmbeddingProvider(
        model_name="google/embeddinggemma-300m",
        fallback_model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_factory=model_factory,
    )

    assert provider.embed_query("context engineering") == [1.0, 2.0, 3.0]
    assert loaded == ["google/embeddinggemma-300m", "sentence-transformers/all-MiniLM-L6-v2"]


def test_embedding_provider_returns_plain_python_floats() -> None:
    provider = EmbeddingProvider(model=FakeNumpyModel())

    vector = provider.embed_query("context engineering")

    assert vector == [0.25, 0.5]
    assert all(type(value) is float for value in vector)
