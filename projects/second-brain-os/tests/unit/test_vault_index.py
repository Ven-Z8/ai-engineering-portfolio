from __future__ import annotations

from pathlib import Path

from second_brain.vault.index import VaultIndex


class FakeEmbeddingProvider:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text)), 1.0]


class FakeCollection:
    def __init__(self) -> None:
        self.deleted: list[dict[str, object]] = []
        self.added: dict[str, object] = {}
        self.query_args: dict[str, object] = {}

    def delete(self, *, where: dict[str, str]) -> None:
        self.deleted.append({"where": where})

    def add(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, str | int]],
    ) -> None:
        self.added = {
            "ids": ids,
            "embeddings": embeddings,
            "documents": documents,
            "metadatas": metadatas,
        }

    def query(
        self,
        *,
        query_embeddings: list[list[float]],
        n_results: int,
        where: dict[str, str] | None = None,
    ) -> dict[str, list[list[object]]]:
        self.query_args = {
            "query_embeddings": query_embeddings,
            "n_results": n_results,
            "where": where,
        }
        return {
            "ids": [["chunk-1"]],
            "documents": [["Context budgets allocate tokens across evidence."]],
            "metadatas": [[{"path": "note.md", "title": "Note", "heading": "Ideas", "chunk_index": 0}]],
            "distances": [[0.12]],
        }


class FakeStateStore:
    def __init__(self) -> None:
        self.hashes: dict[str, str] = {}
        self.recorded: list[tuple[str, str, int]] = []

    def indexed_file_hash(self, path: str) -> str | None:
        return self.hashes.get(path)

    def upsert_indexed_file(self, path: str, content_hash: str, chunk_count: int) -> None:
        self.hashes[path] = content_hash
        self.recorded.append((path, content_hash, chunk_count))


def test_vault_index_chunks_markdown_by_headings(tmp_path: Path) -> None:
    vault = tmp_path / "Brain"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text(
        "# ContextForge\n\nIntro text.\n\n## Token Budgets\n\nAllocate context carefully.\n",
        encoding="utf-8",
    )
    collection = FakeCollection()
    state = FakeStateStore()
    index = VaultIndex(
        vault_path=vault,
        collection=collection,
        embedding_provider=FakeEmbeddingProvider(),
        state_store=state,
    )

    result = index.index()

    assert result.files_indexed == 1
    assert result.chunks_indexed == 2
    assert collection.deleted == [{"where": {"path": str(note)}}]
    assert collection.added["documents"] == ["Intro text.", "Allocate context carefully."]
    assert collection.added["metadatas"] == [
        {"path": str(note), "title": "ContextForge", "heading": "ContextForge", "chunk_index": 0},
        {"path": str(note), "title": "ContextForge", "heading": "Token Budgets", "chunk_index": 1},
    ]
    assert state.recorded[0][0] == str(note)


def test_vault_index_skips_unchanged_files(tmp_path: Path) -> None:
    vault = tmp_path / "Brain"
    vault.mkdir()
    note = vault / "note.md"
    note.write_text("# Stable\n\nSame content.\n", encoding="utf-8")
    collection = FakeCollection()
    state = FakeStateStore()
    index = VaultIndex(
        vault_path=vault,
        collection=collection,
        embedding_provider=FakeEmbeddingProvider(),
        state_store=state,
    )

    first = index.index()
    second = index.index()

    assert first.files_indexed == 1
    assert second.files_indexed == 0
    assert second.files_skipped == 1


def test_vault_index_search_returns_ranked_chunks(tmp_path: Path) -> None:
    collection = FakeCollection()
    index = VaultIndex(
        vault_path=tmp_path,
        collection=collection,
        embedding_provider=FakeEmbeddingProvider(),
        state_store=FakeStateStore(),
    )

    results = index.search("token budget", limit=3)

    assert collection.query_args["n_results"] == 3
    assert results[0].text == "Context budgets allocate tokens across evidence."
    assert results[0].score == 0.88
    assert results[0].path == "note.md"
