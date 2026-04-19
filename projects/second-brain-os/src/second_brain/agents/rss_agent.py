from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser
import structlog

from second_brain.core.models import RawContent, SourceType

logger = structlog.get_logger()


@dataclass
class RSSItem:
    url: str
    title: str
    body: str
    published: str = ""
    feed_title: str = ""


@dataclass
class RSSAgent:
    max_items: int = 10
    max_item_chars: int = 3000

    def fetch_feed(self, feed_url: str) -> list[RawContent]:
        """Fetch up to max_items items from an RSS/Atom feed."""
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:
            logger.warning("rss_parse_failed", url=feed_url, error=str(exc))
            return []

        feed_title = getattr(parsed.feed, "title", feed_url)
        items: list[RawContent] = []
        for entry in parsed.entries[: self.max_items]:
            try:
                items.append(self._entry_to_raw(entry, feed_url, feed_title))
            except Exception as exc:
                logger.warning("rss_entry_failed", url=feed_url, entry=getattr(entry, "link", "?"), error=str(exc))

        return items

    def _entry_to_raw(self, entry: feedparser.FeedParserDict, feed_url: str, feed_title: str) -> RawContent:
        url = getattr(entry, "link", feed_url)
        title = getattr(entry, "title", "Untitled")
        published = getattr(entry, "published", "")

        # Prefer content over summary
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        elif hasattr(entry, "summary"):
            content = entry.summary

        # Strip HTML tags from content
        import re
        content = re.sub(r"<[^>]+>", "", content).strip()
        body = f"Feed: {feed_title}\nPublished: {published}\n\n{content}"

        return RawContent(
            source_type=SourceType.RSS,
            url=url,
            title=title,
            body=body[: self.max_item_chars],
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "feed_url": feed_url,
                "feed_title": feed_title,
                "published": published,
            },
        )
