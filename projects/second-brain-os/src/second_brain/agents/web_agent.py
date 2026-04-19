from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

from second_brain.core.models import RawContent, SourceType

logger = structlog.get_logger()

_PAYWALL_THRESHOLD = 500  # chars — below this, assume blocked content


@dataclass
class WebAgent:
    max_body_chars: int = 50_000
    timeout_seconds: int = 15

    def fetch(self, url: str) -> RawContent:
        html = self._get_html(url)
        title, body = self._extract(html, url)
        domain = urlparse(url).netloc

        if len(body) < _PAYWALL_THRESHOLD:
            logger.warning("web_possible_paywall", url=url, chars=len(body))
            body = f"[Possible paywall or blocked content — only {len(body)} chars extracted]\n\n{body}"

        return RawContent(
            source_type=SourceType.WEB_DOC,
            url=url,
            title=title,
            body=body[: self.max_body_chars],
            fetched_at=datetime.now(timezone.utc),
            metadata={"domain": domain},
        )

    def _get_html(self, url: str) -> str:
        with httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SecondBrainOS/0.1)"},
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text

    def _extract(self, html: str, url: str) -> tuple[str, str]:
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else urlparse(url).netloc

        # Remove noisy elements
        for tag in soup(["nav", "footer", "header", "script", "style", "aside", "advertisement"]):
            tag.decompose()

        # Try <article>, then <main>, then <body>
        content_el = soup.find("article") or soup.find("main") or soup.find("body")
        if content_el is None:
            return title, ""

        text = content_el.get_text(separator="\n", strip=True)
        # Collapse excessive blank lines
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)
        return title, text
