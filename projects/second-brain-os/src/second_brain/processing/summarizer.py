from __future__ import annotations

import re
from pathlib import Path

import structlog
import yaml

from second_brain.core.llm_client import LLMClient
from second_brain.core.models import ProcessedContent, RawContent, SourceType
from second_brain.processing.context_budget import ContextBudget

logger = structlog.get_logger()

_PROMPT_MAP: dict[SourceType, str] = {
    SourceType.GITHUB_REPO: "summarize_repo.yaml",
    SourceType.YOUTUBE: "summarize_video.yaml",
    SourceType.WEB_DOC: "summarize_article.yaml",
    SourceType.RSS: "summarize_article.yaml",
}


class Summarizer:
    def __init__(
        self,
        llm: LLMClient,
        prompts_dir: Path,
        max_tokens: int = 8000,
    ) -> None:
        self.llm = llm
        self.prompts_dir = prompts_dir
        self.budget = ContextBudget(max_tokens=max_tokens)
        self._prompt_cache: dict[str, dict] = {}

    def _load_prompt(self, filename: str) -> dict:
        if filename not in self._prompt_cache:
            path = self.prompts_dir / filename
            with path.open() as f:
                self._prompt_cache[filename] = yaml.safe_load(f)
        return self._prompt_cache[filename]

    async def summarize(self, raw: RawContent) -> ProcessedContent:
        prompt_file = _PROMPT_MAP.get(raw.source_type, "summarize_article.yaml")
        prompt_def = self._load_prompt(prompt_file)

        fitted_body = self.budget.fit(raw.body)
        user_prompt = prompt_def["user"].format(body=fitted_body)
        system_prompt = prompt_def.get("system", "")

        try:
            resp = await self.llm.complete(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=2048,
            )
            parsed = _parse_response(resp.content)
            return ProcessedContent(
                summary=parsed["summary"],
                key_insights=parsed["key_insights"],
                tags=parsed["tags"],
                cost_usd=resp.cost_usd,
                tokens_in=resp.tokens_in,
                tokens_out=resp.tokens_out,
                provider=resp.provider,
            )
        except Exception as exc:
            logger.warning("summarizer_failed", url=raw.url, error=str(exc))
            return _fallback_processed(raw)


def _parse_response(text: str) -> dict:
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    result: dict = {"summary": "", "key_insights": [], "tags": []}
    for section in sections:
        if not section.strip():
            continue
        first_line, _, body = section.partition("\n")
        heading = first_line.strip().lower()
        body = body.strip()

        if heading == "summary":
            result["summary"] = body
        elif "insight" in heading:
            result["key_insights"] = [
                line.lstrip("-• ").strip()
                for line in body.splitlines()
                if line.strip() and line.strip() not in ("-", "•")
            ]
        elif heading == "tags":
            raw_tags = re.split(r"[,\s]+", body.replace("\n", " "))
            result["tags"] = [t.strip("`").strip().lower() for t in raw_tags if t.strip().strip("`")]
        elif "relevance" in heading:
            if result.get("key_insights"):
                result["key_insights"].append(body.strip())

    return result


def _fallback_processed(raw: RawContent) -> ProcessedContent:
    lines = [ln.strip() for ln in raw.body.splitlines() if ln.strip()]
    summary = " ".join(lines[:3])[:300] if lines else raw.title
    return ProcessedContent(
        summary=summary,
        key_insights=[f"Ingested from {raw.source_type.value} (summarization failed)"],
        tags=[raw.source_type.value],
        provider="none",
    )
