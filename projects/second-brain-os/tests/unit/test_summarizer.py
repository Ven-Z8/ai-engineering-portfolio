from __future__ import annotations

import textwrap


from second_brain.core.models import RawContent, SourceType
from second_brain.processing.summarizer import _parse_response, _fallback_processed


def test_parse_response_extracts_all_sections() -> None:
    text = textwrap.dedent("""
        ## Summary
        - Point one
        - Point two

        ## Key Insights
        - Insight one about LangGraph
        - Insight two about memory

        ## Relevance to My Work
        This is relevant because it demonstrates agent patterns.

        ## Tags
        langgraph, multi-agent, graph-state
    """).strip()

    result = _parse_response(text)
    assert "Point one" in result["summary"]
    assert len(result["key_insights"]) >= 2
    assert "langgraph" in result["tags"]
    assert "multi-agent" in result["tags"]


def test_parse_response_handles_missing_sections() -> None:
    result = _parse_response("No structure here.")
    assert result["summary"] == ""
    assert result["key_insights"] == []
    assert result["tags"] == []


def test_fallback_processed_uses_first_body_lines() -> None:
    raw = RawContent(
        source_type=SourceType.WEB_DOC,
        url="https://example.com",
        title="Test Article",
        body="First line of content.\nSecond line.\nThird line.",
    )
    processed = _fallback_processed(raw)
    assert "First line" in processed.summary
    assert processed.provider == "none"


def test_fallback_processed_empty_body_uses_title() -> None:
    raw = RawContent(
        source_type=SourceType.WEB_DOC,
        url="https://example.com",
        title="My Article",
        body="",
    )
    processed = _fallback_processed(raw)
    assert processed.summary == "My Article"
