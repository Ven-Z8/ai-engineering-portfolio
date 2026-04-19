from __future__ import annotations

import asyncio
from pathlib import Path

from second_brain.core.db import StateStore
from second_brain.core.models import ProcessedContent, RawContent, SourceType
from second_brain.core.settings import Settings
from second_brain.orchestration.pipeline import Pipeline


class FakeGitHubAgent:
    def __init__(self, raw: RawContent) -> None:
        self.raw = raw

    def fetch(self, source_url: str) -> RawContent:
        return self.raw


class FakeSummarizer:
    async def summarize(self, raw: RawContent) -> ProcessedContent:
        return ProcessedContent(
            summary=f"Summary for {raw.title}",
            key_insights=["One useful point."],
            tags=["demo"],
            provider="test",
        )


def _make_pipeline(tmp_path: Path, raw: RawContent, db: StateStore | None = None) -> Pipeline:
    settings = Settings(vault_path=tmp_path / "vault", db_path=tmp_path / "state.db")
    pipeline = Pipeline(settings=settings, github_agent=FakeGitHubAgent(raw), db=db)
    pipeline.summarizer = FakeSummarizer()  # type: ignore[assignment]
    pipeline.project_mapper = None  # skip project mapping in unit tests
    return pipeline


def test_pipeline_run_writes_note_for_github_source(tmp_path: Path) -> None:
    raw = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/example/demo",
        title="example/demo",
        body="## README\nDemo repo",
    )
    pipeline = _make_pipeline(tmp_path, raw)
    stats = asyncio.run(pipeline.run({"github_repos": [raw.url]}))

    assert stats.sources_processed == 1
    assert stats.notes_created == 1
    notes = list((tmp_path / "vault" / "04-Resources" / "repos").glob("*.md"))
    assert len(notes) == 1


def test_pipeline_dry_run_does_not_write_note(tmp_path: Path) -> None:
    raw = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/example/demo",
        title="example/demo",
        body="## README\nDemo repo",
    )
    pipeline = _make_pipeline(tmp_path, raw)
    stats = asyncio.run(pipeline.run({"github_repos": [raw.url]}, dry_run=True))

    assert stats.sources_processed == 1
    assert stats.notes_created == 0
    assert not (tmp_path / "vault" / "04-Resources" / "repos").exists()


def test_pipeline_skips_duplicate_source_when_hash_is_unchanged(tmp_path: Path) -> None:
    raw = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/example/demo",
        title="example/demo",
        body="## README\nDemo repo",
    )
    db = StateStore(db_path=tmp_path / "state.db")
    db.upsert_item(
        url=raw.url,
        source_type=raw.source_type.value,
        content_hash=raw.content_hash,
        note_path=str(tmp_path / "vault" / "04-Resources" / "repos" / "demo.md"),
        run_id=1,
    )
    pipeline = _make_pipeline(tmp_path, raw, db=db)
    stats = asyncio.run(pipeline.run({"github_repos": [raw.url]}))

    assert stats.sources_processed == 1
    assert stats.notes_created == 0
    assert stats.notes_skipped == 1
