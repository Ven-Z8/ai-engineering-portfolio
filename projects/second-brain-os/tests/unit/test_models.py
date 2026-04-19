from __future__ import annotations

from second_brain.core.models import ProcessedContent, RawContent, SourceType


def test_raw_content_generates_short_hash() -> None:
    item = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/langchain-ai/langgraph",
        title="langchain-ai/langgraph",
        body="hello world",
    )

    assert len(item.content_hash) == 16


def test_processed_content_normalizes_empty_lists() -> None:
    content = ProcessedContent(summary="Short summary.")

    assert content.key_insights == []
    assert content.tags == []
