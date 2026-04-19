from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from second_brain.core.models import RunStats


@dataclass
class StateStore:
    db_path: Path

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_items (
                    url TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    note_path TEXT NOT NULL,
                    run_id INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_log (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    items_processed INTEGER DEFAULT 0,
                    items_skipped INTEGER DEFAULT 0,
                    notes_created INTEGER DEFAULT 0,
                    tokens_used INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS indexed_files (
                    path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL
                )
                """
            )

    def start_run(self) -> int:
        """Insert a new run row and return the run_id."""
        ts = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO run_log (started_at) VALUES (?)", (ts,)
            )
            return cur.lastrowid or 1

    def finish_run(self, run_id: int, stats: RunStats) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE run_log SET
                    finished_at = ?,
                    items_processed = ?,
                    items_skipped = ?,
                    notes_created = ?,
                    tokens_used = ?,
                    cost_usd = ?
                WHERE run_id = ?
                """,
                (
                    ts,
                    stats.sources_processed,
                    stats.notes_skipped,
                    stats.notes_created,
                    stats.tokens_used,
                    stats.cost_usd,
                    run_id,
                ),
            )

    def last_run(self) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM run_log ORDER BY run_id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def is_processed(self, url: str, content_hash: str, freshness_days: int) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT content_hash, fetched_at FROM processed_items WHERE url = ?",
                (url,),
            ).fetchone()
        if row is None:
            return False
        if row["content_hash"] != content_hash:
            return False
        fetched_at = datetime.fromisoformat(row["fetched_at"])
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - fetched_at).days
        return age_days < freshness_days

    def upsert_item(
        self,
        url: str,
        source_type: str,
        content_hash: str,
        note_path: str,
        run_id: int,
        fetched_at: datetime | None = None,
    ) -> None:
        timestamp = (fetched_at or datetime.now(timezone.utc)).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO processed_items (url, source_type, content_hash, fetched_at, note_path, run_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    source_type=excluded.source_type,
                    content_hash=excluded.content_hash,
                    fetched_at=excluded.fetched_at,
                    note_path=excluded.note_path,
                    run_id=excluded.run_id
                """,
                (url, source_type, content_hash, timestamp, note_path, run_id),
            )

    def indexed_file_hash(self, path: str) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT content_hash FROM indexed_files WHERE path = ?",
                (path,),
            ).fetchone()
        return str(row["content_hash"]) if row else None

    def upsert_indexed_file(self, path: str, content_hash: str, chunk_count: int) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO indexed_files (path, content_hash, indexed_at, chunk_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    content_hash=excluded.content_hash,
                    indexed_at=excluded.indexed_at,
                    chunk_count=excluded.chunk_count
                """,
                (path, content_hash, timestamp, chunk_count),
            )
