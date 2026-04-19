from __future__ import annotations

from datetime import datetime, timedelta, timezone

from second_brain.core.db import StateStore


def test_is_processed_false_for_new_url(tmp_path) -> None:
    db = StateStore(db_path=tmp_path / "state.db")

    assert db.is_processed("https://example.com/a", "hash-1", freshness_days=7) is False


def test_is_processed_true_for_same_hash_within_freshness_window(tmp_path) -> None:
    db = StateStore(db_path=tmp_path / "state.db")
    db.upsert_item(
        url="https://example.com/a",
        source_type="github_repo",
        content_hash="hash-1",
        note_path="/vault/note.md",
        run_id=1,
    )

    assert db.is_processed("https://example.com/a", "hash-1", freshness_days=7) is True


def test_is_processed_false_for_different_hash(tmp_path) -> None:
    db = StateStore(db_path=tmp_path / "state.db")
    db.upsert_item(
        url="https://example.com/a",
        source_type="github_repo",
        content_hash="hash-1",
        note_path="/vault/note.md",
        run_id=1,
    )

    assert db.is_processed("https://example.com/a", "hash-2", freshness_days=7) is False


def test_is_processed_false_when_entry_is_stale(tmp_path) -> None:
    db = StateStore(db_path=tmp_path / "state.db")
    db.upsert_item(
        url="https://example.com/a",
        source_type="github_repo",
        content_hash="hash-1",
        note_path="/vault/note.md",
        run_id=1,
        fetched_at=datetime.now(timezone.utc) - timedelta(days=10),
    )

    assert db.is_processed("https://example.com/a", "hash-1", freshness_days=7) is False
