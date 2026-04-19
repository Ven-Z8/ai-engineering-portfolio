from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from second_brain.processing.project_mapper import ProjectMapper


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    config = {
        "projects": [
            {
                "folder": "03-AgentOrchestra",
                "name": "AgentOrchestra",
                "description": "Multi-agent orchestration",
                "key_technologies": ["multi-agent", "langgraph", "anthropic"],
            },
            {
                "folder": "02-RAGBench-Pro",
                "name": "RAGBench Pro",
                "description": "RAG evaluation",
                "key_technologies": ["rag", "retrieval", "embeddings", "evaluation"],
            },
        ]
    }
    p = tmp_path / "portfolio_projects.yaml"
    p.write_text(yaml.dump(config), encoding="utf-8")
    return p


def test_mapper_matches_project_by_keywords(config_path: Path) -> None:
    mapper = ProjectMapper(config_path=config_path)
    matched = mapper.map("langgraph multi-agent orchestration system", tags=["langgraph"])
    assert "03-AgentOrchestra" in matched


def test_mapper_returns_empty_for_unrelated_text(config_path: Path) -> None:
    mapper = ProjectMapper(config_path=config_path)
    matched = mapper.map("unrelated topic about cooking recipes", tags=["food"])
    assert matched == []


def test_mapper_caps_at_five_results(config_path: Path) -> None:
    mapper = ProjectMapper(config_path=config_path)
    matched = mapper.map("rag retrieval embeddings evaluation langgraph multi-agent anthropic", tags=[])
    assert len(matched) <= 5
