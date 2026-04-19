from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import anthropic
import httpx
import structlog

from second_brain.core.settings import Settings

logger = structlog.get_logger()

# Cost per 1M tokens (input/output) for tracking purposes
_MODEL_COSTS: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.25, 1.25),
    "claude-opus-4-7": (15.0, 75.0),
}


def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    in_rate, out_rate = _MODEL_COSTS.get(model, (3.0, 15.0))
    return (tokens_in * in_rate + tokens_out * out_rate) / 1_000_000


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    provider: str  # "anthropic" | "openrouter"
    latency_ms: int


class HarnessLLMError(Exception):
    pass


@dataclass
class LLMClient:
    settings: Settings
    _total_cost_usd: float = field(default=0.0, init=False)

    async def complete(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        chosen_model = model or self.settings.default_model
        t0 = time.monotonic()

        # Try Anthropic first
        try:
            response = await self._call_anthropic(prompt, system, chosen_model, max_tokens)
            self._total_cost_usd += response.cost_usd
            logger.debug(
                "llm_call_ok",
                provider="anthropic",
                model=chosen_model,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                cost_usd=response.cost_usd,
                latency_ms=response.latency_ms,
            )
            return response
        except (anthropic.RateLimitError, anthropic.APIError, anthropic.APIConnectionError) as exc:
            logger.warning("anthropic_failed", error=str(exc), model=chosen_model)

        # Fallback to OpenRouter
        if self.settings.openrouter_api_key:
            try:
                response = await self._call_openrouter(
                    prompt, system, self.settings.fallback_model, max_tokens, t0
                )
                self._total_cost_usd += response.cost_usd
                logger.debug(
                    "llm_call_ok",
                    provider="openrouter",
                    model=self.settings.fallback_model,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    cost_usd=response.cost_usd,
                )
                return response
            except Exception as exc:
                logger.warning("openrouter_failed", error=str(exc))

        raise HarnessLLMError(f"All LLM providers failed for model {chosen_model}")

    async def _call_anthropic(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
    ) -> LLMResponse:
        t0 = time.monotonic()
        client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        result = await client.messages.create(**kwargs)
        latency_ms = int((time.monotonic() - t0) * 1000)
        tokens_in = result.usage.input_tokens
        tokens_out = result.usage.output_tokens
        content_text = result.content[0].text if result.content else ""

        return LLMResponse(
            content=content_text,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=_estimate_cost(model, tokens_in, tokens_out),
            provider="anthropic",
            latency_ms=latency_ms,
        )

    async def _call_openrouter(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
        t0: float,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "max_tokens": max_tokens, "messages": messages}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = int((time.monotonic() - t0) * 1000)
        choice = data["choices"][0]
        content_text = choice["message"]["content"]
        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)

        return LLMResponse(
            content=content_text,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=_estimate_cost(model, tokens_in, tokens_out),
            provider="openrouter",
            latency_ms=latency_ms,
        )

    @property
    def total_cost_usd(self) -> float:
        return self._total_cost_usd
