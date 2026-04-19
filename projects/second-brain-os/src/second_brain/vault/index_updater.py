from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import structlog

from second_brain.core.models import RunStats

logger = structlog.get_logger()


class IndexUpdater:
    """Maintains 07-Meta/pipeline-log.md — one line per run, appended."""

    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self.meta_dir = vault_path / "07-Meta"
        self.log_path = self.meta_dir / "pipeline-log.md"
        self.moc_path = self.meta_dir / "MOC-Home.md"

    def append_run_log(self, stats: RunStats) -> None:
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("# Pipeline Log\n\n| Date | Run | Created | Skipped | Tokens | Cost |\n|---|---|---|---|---|---|\n", encoding="utf-8")

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        line = f"| {ts} | #{stats.run_id} | {stats.notes_created} | {stats.notes_skipped} | {stats.tokens_used:,} | ${stats.cost_usd:.4f} |\n"
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line)
        logger.info("pipeline_log_updated", run_id=stats.run_id)

    def ensure_moc(self) -> None:
        """Create MOC-Home.md if it doesn't exist."""
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        if not self.moc_path.exists():
            self.moc_path.write_text(
                "# Second Brain — Map of Content\n\n"
                "## Active Projects\n"
                "- [[02-Projects/00-Portfolio-Overview]]\n\n"
                "## Daily Notes\n"
                "- [[01-Daily/]]\n\n"
                "## Resources\n"
                "- [[04-Resources/repos/]]\n"
                "- [[04-Resources/videos/]]\n"
                "- [[04-Resources/articles/]]\n\n"
                "## Pipeline\n"
                "- [[07-Meta/pipeline-log]]\n",
                encoding="utf-8",
            )
