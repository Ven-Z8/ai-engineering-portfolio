from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any


class SourceType(str, Enum):
    GITHUB_REPO = "github_repo"
    WEB_DOC = "web_doc"
    YOUTUBE = "youtube"
    RSS = "rss"


class RawContent:
    __slots__ = (
        "source_type",
        "url",
        "title",
        "body",
        "fetched_at",
        "metadata",
        "content_hash",
    )

    def __init__(
        self,
        source_type: SourceType,
        url: str,
        title: str,
        body: str,
        fetched_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        content_hash: str = "",
    ) -> None:
        self.source_type = source_type
        self.url = url
        self.title = title
        self.body = body
        self.fetched_at = fetched_at or datetime.now(timezone.utc)
        self.metadata = metadata or {}
        self.content_hash = content_hash or hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


class ProcessedContent:
    __slots__ = (
        "summary",
        "key_insights",
        "tags",
        "project_relevance",
        "relevance_note",
        "cost_usd",
        "tokens_in",
        "tokens_out",
        "provider",
    )

    def __init__(
        self,
        summary: str,
        key_insights: list[str] | None = None,
        tags: list[str] | None = None,
        project_relevance: list[str] | None = None,
        relevance_note: str = "",
        cost_usd: float = 0.0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        provider: str = "none",
    ) -> None:
        self.summary = summary
        self.key_insights = key_insights or []
        self.tags = tags or []
        self.project_relevance = project_relevance or []
        self.relevance_note = relevance_note
        self.cost_usd = cost_usd
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.provider = provider


class RunStats:
    __slots__ = (
        "run_id",
        "started_at",
        "finished_at",
        "sources_processed",
        "notes_created",
        "notes_updated",
        "notes_skipped",
        "notes_fallback",
        "tokens_used",
        "cost_usd",
        "duration_seconds",
        "provider_counts",
        "failed_count",
    )

    def __init__(self) -> None:
        self.run_id: int = 0
        self.started_at: datetime = datetime.now(timezone.utc)
        self.finished_at: datetime | None = None
        self.sources_processed: int = 0
        self.notes_created: int = 0
        self.notes_updated: int = 0
        self.notes_skipped: int = 0
        self.notes_fallback: int = 0
        self.tokens_used: int = 0
        self.cost_usd: float = 0.0
        self.duration_seconds: float = 0.0
        self.provider_counts: dict[str, int] = {}
        self.failed_count: int = 0

    def add_processed(self, processed: ProcessedContent) -> None:
        self.tokens_used += processed.tokens_in + processed.tokens_out
        self.cost_usd += processed.cost_usd
        self.provider_counts[processed.provider] = self.provider_counts.get(processed.provider, 0) + 1
