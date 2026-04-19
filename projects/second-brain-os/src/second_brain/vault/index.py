from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Protocol

from second_brain.core.db import StateStore
from second_brain.core.settings import Settings
from second_brain.embeddings.provider import EmbeddingProvider


class CollectionLike(Protocol):
    def delete(self, *, where: dict[str, str]) -> None:
        ...

    def add(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, str | int]],
    ) -> None:
        ...

    def query(
        self,
        *,
        query_embeddings: list[list[float]],
        n_results: int,
        where: dict[str, str] | None = None,
    ) -> dict[str, list[list[object]]]:
        ...


class EmbeddingProviderLike(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


@dataclass
class IndexStats:
    files_indexed: int = 0
    files_skipped: int = 0
    chunks_indexed: int = 0


@dataclass
class SearchResult:
    text: str
    path: str
    title: str
    heading: str
    score: float
    chunk_index: int


@dataclass
class MarkdownChunk:
    text: str
    title: str
    heading: str
    chunk_index: int


@dataclass
class VaultIndex:
    vault_path: Path
    collection: CollectionLike
    embedding_provider: EmbeddingProviderLike
    state_store: StateStore

    @classmethod
    def from_settings(cls, settings: Settings) -> "VaultIndex":
        import chromadb

        chroma_path = settings.chroma_path
        chroma_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(chroma_path))
        collection = client.get_or_create_collection(name="brain")
        return cls(
            vault_path=settings.vault_path,
            collection=collection,
            embedding_provider=EmbeddingProvider(
                model_name=settings.embedding_model,
                fallback_model_name=settings.fallback_embedding_model,
                truncate_dim=settings.embedding_truncate_dim,
            ),
            state_store=StateStore(settings.db_path),
        )

    def index(self) -> IndexStats:
        stats = IndexStats()
        for path in sorted(self.vault_path.rglob("*.md")):
            if self._should_ignore(path):
                continue
            content = path.read_text(encoding="utf-8")
            content_hash = sha256(content.encode("utf-8")).hexdigest()
            if self.state_store.indexed_file_hash(str(path)) == content_hash:
                stats.files_skipped += 1
                continue

            chunks = self._chunk_markdown(content)
            self.collection.delete(where={"path": str(path)})
            if chunks:
                documents = [chunk.text for chunk in chunks]
                embeddings = self.embedding_provider.embed_documents(documents)
                ids = [self._chunk_id(path, chunk.chunk_index, content_hash) for chunk in chunks]
                metadatas = [
                    {
                        "path": str(path),
                        "title": chunk.title,
                        "heading": chunk.heading,
                        "chunk_index": chunk.chunk_index,
                    }
                    for chunk in chunks
                ]
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                )

            self.state_store.upsert_indexed_file(str(path), content_hash, len(chunks))
            stats.files_indexed += 1
            stats.chunks_indexed += len(chunks)
        return stats

    def search(self, query: str, limit: int = 5, project: str | None = None) -> list[SearchResult]:
        where = {"project": project} if project else None
        raw = self.collection.query(
            query_embeddings=[self.embedding_provider.embed_query(query)],
            n_results=limit,
            where=where,
        )
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        results: list[SearchResult] = []
        for text, metadata, distance in zip(documents, metadatas, distances, strict=False):
            meta = metadata if isinstance(metadata, dict) else {}
            numeric_distance = float(distance) if distance is not None else 1.0
            results.append(
                SearchResult(
                    text=str(text),
                    path=str(meta.get("path", "")),
                    title=str(meta.get("title", "")),
                    heading=str(meta.get("heading", "")),
                    score=max(0.0, min(1.0, 1.0 - numeric_distance)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                )
            )
        return results

    def _chunk_markdown(self, content: str) -> list[MarkdownChunk]:
        title = self._title_for(content)
        current_heading = title
        current_lines: list[str] = []
        chunks: list[MarkdownChunk] = []

        def flush() -> None:
            text = "\n".join(current_lines).strip()
            if text:
                chunks.append(
                    MarkdownChunk(
                        text=text,
                        title=title,
                        heading=current_heading,
                        chunk_index=len(chunks),
                    )
                )
            current_lines.clear()

        for line in content.splitlines():
            heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if heading_match:
                flush()
                current_heading = heading_match.group(2).strip()
                continue
            current_lines.append(line)
        flush()
        return chunks

    def _title_for(self, content: str) -> str:
        for line in content.splitlines():
            match = re.match(r"^#\s+(.+?)\s*$", line)
            if match:
                return match.group(1).strip()
        return "Untitled"

    def _chunk_id(self, path: Path, chunk_index: int, content_hash: str) -> str:
        raw = f"{path}:{chunk_index}:{content_hash}"
        return sha256(raw.encode("utf-8")).hexdigest()

    def _should_ignore(self, path: Path) -> bool:
        ignored_parts = {".obsidian", ".openclaw", ".git", "__pycache__"}
        return any(part in ignored_parts for part in path.parts)
