from __future__ import annotations

from unittest.mock import MagicMock, patch

from second_brain.agents.rss_agent import RSSAgent
from second_brain.agents.web_agent import WebAgent
from second_brain.agents.youtube_agent import YouTubeAgent
from second_brain.core.models import SourceType


# ── RSS Agent ──────────────────────────────────────────────────────────────────

def test_rss_agent_returns_empty_list_on_parse_failure() -> None:
    agent = RSSAgent()
    with patch("second_brain.agents.rss_agent.feedparser.parse", side_effect=Exception("network error")):
        result = agent.fetch_feed("https://example.com/feed.rss")
    assert result == []


def test_rss_agent_limits_items(tmp_path) -> None:
    mock_feed = MagicMock()
    mock_feed.feed.title = "Test Feed"
    mock_feed.entries = [
        MagicMock(
            link=f"https://example.com/{i}",
            title=f"Item {i}",
            summary=f"Content {i}",
            published="2026-04-18",
        )
        for i in range(20)
    ]
    # Remove content attr so it falls back to summary
    for entry in mock_feed.entries:
        del entry.content

    with patch("second_brain.agents.rss_agent.feedparser.parse", return_value=mock_feed):
        agent = RSSAgent(max_items=5)
        result = agent.fetch_feed("https://example.com/feed.rss")

    assert len(result) == 5
    for item in result:
        assert item.source_type == SourceType.RSS


# ── Web Agent ─────────────────────────────────────────────────────────────────

def test_web_agent_extracts_title_and_body() -> None:
    html = """
    <html>
    <head><title>Test Article</title></head>
    <body>
      <nav>Nav stuff</nav>
      <article>
        <p>This is the article content with enough characters to pass the paywall check.</p>
        <p>Second paragraph with more content here.</p>
      </article>
    </body>
    </html>
    """
    with patch("second_brain.agents.web_agent.httpx.Client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_client.return_value.__enter__.return_value.get.return_value = mock_resp

        agent = WebAgent()
        raw = agent.fetch("https://example.com/article")

    assert raw.title == "Test Article"
    assert "article content" in raw.body
    assert raw.source_type == SourceType.WEB_DOC


# ── YouTube Agent ─────────────────────────────────────────────────────────────

def test_youtube_agent_extracts_video_id_from_watch_url() -> None:
    agent = YouTubeAgent()
    vid_id = agent._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert vid_id == "dQw4w9WgXcQ"


def test_youtube_agent_extracts_video_id_from_short_url() -> None:
    agent = YouTubeAgent()
    vid_id = agent._extract_video_id("https://youtu.be/dQw4w9WgXcQ")
    assert vid_id == "dQw4w9WgXcQ"
