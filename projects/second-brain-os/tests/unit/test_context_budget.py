from __future__ import annotations

from second_brain.processing.context_budget import ContextBudget


def test_fits_returns_true_for_short_text() -> None:
    budget = ContextBudget(max_tokens=1000)
    assert budget.fits("Hello world") is True


def test_fits_returns_false_for_long_text() -> None:
    budget = ContextBudget(max_tokens=5)
    long = "word " * 100
    assert budget.fits(long) is False


def test_fit_truncates_to_budget() -> None:
    budget = ContextBudget(max_tokens=10)
    long = "word " * 500
    result = budget.fit(long)
    assert "[...truncated" in result
    # Allow small margin: tiktoken decode round-trip can add 1-2 tokens from whitespace
    assert budget.count_tokens(result.split("[")[0]) <= 12


def test_fit_preserves_short_text_unchanged() -> None:
    budget = ContextBudget(max_tokens=1000)
    text = "Short text that fits."
    result = budget.fit(text)
    assert result == text
