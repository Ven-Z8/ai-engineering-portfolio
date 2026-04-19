from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
import structlog
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

from second_brain.core.models import RawContent, SourceType

logger = structlog.get_logger()

_VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_\-]{11})"
)


@dataclass
class YouTubeAgent:
    max_transcript_chars: int = 40_000

    def fetch(self, url: str) -> RawContent:
        video_id = self._extract_video_id(url)
        transcript = self._get_transcript(video_id)
        meta = self._get_oembed(url)

        title = meta.get("title", f"YouTube: {video_id}")
        channel = meta.get("author_name", "Unknown")
        body = f"Channel: {channel}\n\n## Transcript\n\n{transcript}"

        return RawContent(
            source_type=SourceType.YOUTUBE,
            url=url,
            title=title,
            body=body,
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "video_id": video_id,
                "channel": channel,
                "provider": meta.get("provider_name", "YouTube"),
            },
        )

    def _extract_video_id(self, url: str) -> str:
        match = _VIDEO_ID_RE.search(url)
        if match:
            return match.group(1)
        # Try query param
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        vid_list = params.get("v", [])
        if vid_list:
            return vid_list[0]
        raise ValueError(f"Cannot extract video ID from URL: {url}")

    def _get_transcript(self, video_id: str) -> str:
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            # Prefer English; fall back to first available
            try:
                transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
            except Exception:
                transcript = transcript_list.find_manually_created_transcript(
                    [t.language_code for t in transcript_list]
                )
            snippets = transcript.fetch()
            text = " ".join(s.text for s in snippets)
            return text[: self.max_transcript_chars]
        except (NoTranscriptFound, TranscriptsDisabled) as exc:
            logger.warning("youtube_no_transcript", video_id=video_id, error=str(exc))
            return f"[Transcript unavailable: {exc}]"
        except Exception as exc:
            logger.warning("youtube_transcript_error", video_id=video_id, error=str(exc))
            return f"[Transcript fetch failed: {exc}]"

    def _get_oembed(self, url: str) -> dict:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    "https://www.youtube.com/oembed",
                    params={"url": url, "format": "json"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as exc:
            logger.warning("youtube_oembed_failed", url=url, error=str(exc))
        return {}
