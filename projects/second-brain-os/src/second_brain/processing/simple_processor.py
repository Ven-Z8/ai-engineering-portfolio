from __future__ import annotations

from second_brain.core.models import ProcessedContent, RawContent


class SimpleProcessor:
    def process(self, raw: RawContent) -> ProcessedContent:
        lines = [line.strip() for line in raw.body.splitlines() if line.strip()]
        first_content_line = lines[1] if len(lines) > 1 else (lines[0] if lines else raw.title)
        summary = first_content_line[:180]
        return ProcessedContent(
            summary=summary,
            key_insights=[f"Ingested from {raw.source_type.value}"],
            tags=[raw.source_type.value],
        )
