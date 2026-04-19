from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from rich.console import Console
from rich.table import Table

from second_brain.agents.github_agent import GitHubRepoAgent
from second_brain.agents.rss_agent import RSSAgent
from second_brain.agents.web_agent import WebAgent
from second_brain.agents.youtube_agent import YouTubeAgent
from second_brain.core.db import StateStore
from second_brain.core.llm_client import HarnessLLMError, LLMClient
from second_brain.core.models import ProcessedContent, RawContent, RunStats
from second_brain.core.settings import Settings
from second_brain.processing.project_mapper import ProjectMapper
from second_brain.processing.summarizer import Summarizer
from second_brain.vault.daily_note import DailyNoteWriter
from second_brain.vault.index_updater import IndexUpdater
from second_brain.vault.note_writer import NoteWriter

logger = structlog.get_logger()
console = Console()


class Pipeline:
    def __init__(
        self,
        settings: Settings,
        llm: LLMClient | None = None,
        github_agent: GitHubRepoAgent | None = None,
        youtube_agent: YouTubeAgent | None = None,
        web_agent: WebAgent | None = None,
        rss_agent: RSSAgent | None = None,
        db: StateStore | None = None,
    ) -> None:
        self.settings = settings
        self.llm = llm or LLMClient(settings=settings)
        self.github_agent = github_agent or GitHubRepoAgent()
        self.youtube_agent = youtube_agent or YouTubeAgent()
        self.web_agent = web_agent or WebAgent()
        self.rss_agent = rss_agent or RSSAgent()
        self.db = db or StateStore(db_path=settings.db_path)
        self.writer = NoteWriter(vault_path=settings.vault_path)
        self.daily_writer = DailyNoteWriter(vault_path=settings.vault_path)
        self.index_updater = IndexUpdater(vault_path=settings.vault_path)

        prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts"
        self.summarizer = Summarizer(llm=self.llm, prompts_dir=prompts_dir)

        portfolio_config = Path(__file__).parent.parent.parent.parent / "config" / "portfolio_projects.yaml"
        self.project_mapper = ProjectMapper(config_path=portfolio_config) if portfolio_config.exists() else None

    async def run(self, sources: dict[str, list[str]], dry_run: bool = False) -> RunStats:
        stats = RunStats()
        stats.started_at = datetime.now(timezone.utc)
        run_id = self.db.start_run()
        stats.run_id = run_id

        self.index_updater.ensure_moc()

        # Gather all raw items from all agents in parallel
        raw_items = await self._fetch_all(sources)

        new_notes: list[tuple[RawContent, ProcessedContent, Path]] = []

        for raw in raw_items:
            stats.sources_processed += 1
            if self.db.is_processed(raw.url, raw.content_hash, self.settings.freshness_days):
                stats.notes_skipped += 1
                continue
            if dry_run:
                continue

            try:
                processed = await self.summarizer.summarize(raw)
            except HarnessLLMError:
                # Write raw to 00-Inbox
                inbox = self.settings.vault_path / "00-Inbox"
                inbox.mkdir(parents=True, exist_ok=True)
                inbox_file = inbox / f"{raw.fetched_at:%Y-%m-%d}-{raw.content_hash}.md"
                inbox_file.write_text(raw.body, encoding="utf-8")
                stats.notes_fallback += 1
                continue

            # Map to portfolio projects
            if self.project_mapper:
                processed.project_relevance = self.project_mapper.map(
                    processed.summary + " " + " ".join(processed.key_insights),
                    processed.tags,
                )

            note_path = self.writer.write(raw, processed)
            self.db.upsert_item(
                url=raw.url,
                source_type=raw.source_type.value,
                content_hash=raw.content_hash,
                note_path=str(note_path),
                run_id=run_id,
            )
            stats.notes_created += 1
            stats.add_processed(processed)
            new_notes.append((raw, processed, note_path))

        stats.finished_at = datetime.now(timezone.utc)
        stats.duration_seconds = (stats.finished_at - stats.started_at).total_seconds()

        if not dry_run:
            self.daily_writer.write(stats, new_notes)
            self.index_updater.append_run_log(stats)

        self.db.finish_run(run_id, stats)
        self._print_table(stats)
        return stats

    async def _fetch_all(self, sources: dict[str, list[str]]) -> list[RawContent]:
        tasks: list[Any] = []

        for url in sources.get("github_repos", []):
            tasks.append(self._safe_fetch(self.github_agent.fetch, url))

        for url in sources.get("youtube", []):
            tasks.append(self._safe_fetch(self.youtube_agent.fetch, url))

        for url in sources.get("web", []):
            tasks.append(self._safe_fetch(self.web_agent.fetch, url))

        for feed_url in sources.get("rss_feeds", []):
            tasks.append(self._safe_fetch_feed(feed_url))

        results = await asyncio.gather(*tasks, return_exceptions=False)
        raw_items: list[RawContent] = []
        for result in results:
            if isinstance(result, list):
                raw_items.extend(result)
            elif isinstance(result, RawContent):
                raw_items.append(result)
        return raw_items

    async def _safe_fetch(self, fetch_fn: Any, url: str) -> RawContent | None:
        try:
            return await asyncio.to_thread(fetch_fn, url)
        except Exception as exc:
            logger.warning("agent_fetch_failed", url=url, error=str(exc))
            return None

    async def _safe_fetch_feed(self, feed_url: str) -> list[RawContent]:
        try:
            return await asyncio.to_thread(self.rss_agent.fetch_feed, feed_url)
        except Exception as exc:
            logger.warning("rss_fetch_failed", feed_url=feed_url, error=str(exc))
            return []

    def _print_table(self, stats: RunStats) -> None:
        table = Table(title=f"Second Brain OS — Run #{stats.run_id}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        duration_str = (
            f"{int(stats.duration_seconds // 60)}m {int(stats.duration_seconds % 60)}s"
            if stats.duration_seconds >= 60
            else f"{stats.duration_seconds:.1f}s"
        )
        table.add_row("Sources processed", str(stats.sources_processed))
        table.add_row("Notes created", str(stats.notes_created))
        table.add_row("Notes skipped (dupe)", str(stats.notes_skipped))
        table.add_row("Inbox fallback", str(stats.notes_fallback))
        table.add_row("Tokens used", f"{stats.tokens_used:,}")
        table.add_row("Cost", f"${stats.cost_usd:.4f}")
        table.add_row("Duration", duration_str)
        providers = ", ".join(f"{k}({v})" for k, v in stats.provider_counts.items())
        table.add_row("Providers", providers or "none")

        console.print(table)
