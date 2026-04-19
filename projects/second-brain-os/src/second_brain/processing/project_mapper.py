from __future__ import annotations

import re
from pathlib import Path

import structlog
import yaml

logger = structlog.get_logger()


class ProjectMapper:
    """Maps note content to relevant portfolio projects via keyword intersection.

    Phase 1: keyword matching. Phase 2: embedding cosine similarity.
    """

    def __init__(self, config_path: Path) -> None:
        self._projects = self._load(config_path)

    def _load(self, path: Path) -> list[dict]:
        with path.open() as f:
            return yaml.safe_load(f)["projects"]

    def map(self, text: str, tags: list[str]) -> list[str]:
        """Return list of project folder names that match the content."""
        normalized = (text + " " + " ".join(tags)).lower()
        words = set(re.findall(r"[a-z0-9][a-z0-9\-]+", normalized))

        matched: list[str] = []
        for project in self._projects:
            project_keywords: set[str] = set()
            for tech in project.get("key_technologies", []):
                project_keywords.update(re.findall(r"[a-z0-9][a-z0-9\-]+", tech.lower()))
            project_keywords.update(
                re.findall(r"[a-z0-9][a-z0-9\-]+", project.get("name", "").lower())
            )

            overlap = words & project_keywords
            if len(overlap) >= 2:
                matched.append(project["folder"])

        return matched[:5]  # cap at 5 projects per note
