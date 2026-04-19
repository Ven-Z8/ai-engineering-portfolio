from __future__ import annotations

from datetime import date
from pathlib import Path

from second_brain.core.models import ProcessedContent, RawContent, RunStats, SourceType
from second_brain.vault.daily_note import DailyNoteWriter


def _make_stats() -> RunStats:
    stats = RunStats()
    stats.run_id = 1
    stats.sources_processed = 3
    stats.notes_created = 2
    stats.notes_skipped = 1
    stats.duration_seconds = 45.0
    stats.cost_usd = 0.012
    stats.tokens_used = 800
    stats.provider_counts = {"anthropic": 2}
    return stats


def test_daily_note_creates_file_in_daily_dir(tmp_path: Path) -> None:
    writer = DailyNoteWriter(vault_path=tmp_path / "vault")
    stats = _make_stats()
    note_path = writer.write(stats, [], run_date=date(2026, 4, 18))

    assert note_path.exists()
    assert note_path.name == "2026-04-18.md"
    assert note_path.parent.name == "01-Daily"


def test_daily_note_contains_pipeline_summary(tmp_path: Path) -> None:
    writer = DailyNoteWriter(vault_path=tmp_path / "vault")
    stats = _make_stats()
    note_path = writer.write(stats, [], run_date=date(2026, 4, 18))

    content = note_path.read_text()
    assert "Pipeline Summary" in content
    assert "3 sources" in content
    assert "$0.012" in content


def test_daily_note_lists_new_notes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    writer = DailyNoteWriter(vault_path=vault)
    raw = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/example/repo",
        title="example/repo",
        body="content",
    )
    processed = ProcessedContent(
        summary="Summary line one\nline two",
        key_insights=["Insight A"],
        tags=["python"],
    )
    note_path = vault / "04-Resources" / "repos" / "example-repo.md"

    stats = _make_stats()
    written_path = writer.write(stats, [(raw, processed, note_path)], run_date=date(2026, 4, 18))
    content = written_path.read_text()

    assert "New Notes" in content
    assert "example-repo" in content
