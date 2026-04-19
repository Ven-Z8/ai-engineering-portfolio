from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from second_brain.core.models import ProcessedContent, RawContent, SourceType
from second_brain.vault.note_writer import NoteWriter


def test_note_writer_routes_github_notes_to_projects(tmp_path: Path) -> None:
    writer = NoteWriter(vault_path=tmp_path)
    item = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/langchain-ai/langgraph",
        title="langchain-ai/langgraph",
        body="## README\nLangGraph README",
        fetched_at=datetime(2026, 4, 19, 0, 0, 0, tzinfo=timezone.utc),
        metadata={"repo_name": "langgraph"},
    )
    processed = ProcessedContent(
        summary="Stateful agent framework.",
        key_insights=["Supports graph-based orchestration."],
        tags=["langgraph", "agents"],
    )

    note_path = writer.write(item, processed)

    assert note_path == tmp_path / "04-Resources" / "repos" / "2026-04-19-langchain-ai-langgraph.md"
    content = note_path.read_text(encoding="utf-8")
    assert "source_type: github_repo" in content
    assert "content_hash:" in content
    assert "## Summary" in content
    assert "## Raw Extract" in content
