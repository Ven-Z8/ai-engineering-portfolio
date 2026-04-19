from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from second_brain.core.models import ProcessedContent, RawContent, SourceType


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "note"


@dataclass
class NoteWriter:
    vault_path: Path

    def write(self, raw: RawContent, processed: ProcessedContent) -> Path:
        target_dir = self.target_directory(raw.source_type)
        target_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{raw.fetched_at:%Y-%m-%d}-{slugify(raw.title)}.md"
        note_path = target_dir / file_name
        note_path.write_text(self.render(raw, processed), encoding="utf-8")
        return note_path

    def target_directory(self, source_type: SourceType) -> Path:
        if source_type is SourceType.GITHUB_REPO:
            return self.vault_path / "04-Resources" / "repos"
        if source_type is SourceType.WEB_DOC:
            return self.vault_path / "04-Resources" / "articles"
        if source_type is SourceType.RSS:
            return self.vault_path / "04-Resources" / "articles"
        return self.vault_path / "04-Resources" / "videos"

    def render(self, raw: RawContent, processed: ProcessedContent) -> str:
        frontmatter = [
            "---",
            f'title: "{raw.title}"',
            f"source_type: {raw.source_type.value}",
            f"source_url: {raw.url}",
            f"fetched_at: {raw.fetched_at:%Y-%m-%dT%H:%M:%SZ}",
            f"content_hash: {raw.content_hash}",
            "tags:",
        ]
        for tag in sorted(set(processed.tags + [raw.source_type.value])):
            frontmatter.append(f"  - {tag}")
        frontmatter.extend(["---", ""])

        insights = "\n".join(f"- {line}" for line in processed.key_insights) or "- None"
        metadata_lines = "\n".join(f"- **{k}**: {v}" for k, v in sorted(raw.metadata.items())) or "- None"
        return "\n".join(
            frontmatter
            + [
                f"# {raw.title}",
                "",
                "## Summary",
                processed.summary,
                "",
                "## Key Insights",
                insights,
                "",
                "## Source Metadata",
                metadata_lines,
                "",
                "## Raw Extract",
                raw.body,
                "",
            ]
        )
