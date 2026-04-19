from __future__ import annotations

import tiktoken


class ContextBudget:
    """Enforces token limits before every Claude call — core context engineering primitive."""

    def __init__(self, max_tokens: int = 8000, model: str = "claude-sonnet-4-6") -> None:
        self.max_tokens = max_tokens
        # cl100k_base is the closest tiktoken encoding for Claude models
        try:
            self._enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._enc = None

    def count_tokens(self, text: str) -> int:
        if self._enc is None:
            return len(text) // 4  # rough fallback
        return len(self._enc.encode(text))

    def fits(self, text: str) -> bool:
        return self.count_tokens(text) <= self.max_tokens

    def fit(self, text: str) -> str:
        """Truncate text to fit within budget, preserving structure from the top."""
        if self._enc is None:
            # Rough char-based truncation
            char_limit = self.max_tokens * 4
            return text[:char_limit] + ("\n\n[...truncated to fit context budget...]" if len(text) > char_limit else "")

        tokens = self._enc.encode(text)
        if len(tokens) <= self.max_tokens:
            return text

        truncated = self._enc.decode(tokens[: self.max_tokens])
        return truncated + "\n\n[...truncated to fit context budget...]"
