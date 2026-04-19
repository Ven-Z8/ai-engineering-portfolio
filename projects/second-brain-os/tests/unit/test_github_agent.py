from __future__ import annotations

from pathlib import Path

from second_brain.agents.github_agent import GitHubRepoAgent


def test_fetch_from_checkout_uses_readme_and_structure(tmp_path: Path) -> None:
    repo_dir = tmp_path / "langgraph"
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("# LangGraph\n\nStateful agents.", encoding="utf-8")
    (repo_dir / "pyproject.toml").write_text("[project]\nname='langgraph'\n", encoding="utf-8")
    docs_dir = repo_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Docs", encoding="utf-8")

    agent = GitHubRepoAgent()
    item = agent.fetch_from_checkout(
        "https://github.com/langchain-ai/langgraph",
        repo_dir,
    )

    assert item.title == "langchain-ai/langgraph"
    assert "## README" in item.body
    assert "## File Structure Preview" in item.body
    assert "`pyproject.toml`" in item.body


def test_structure_preview_filters_generated_and_hidden_noise(tmp_path: Path) -> None:
    repo_dir = tmp_path / "clean-demo"
    repo_dir.mkdir()
    (repo_dir / "README.md").write_text("# Demo", encoding="utf-8")
    (repo_dir / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (repo_dir / ".python-version").write_text("3.14\n", encoding="utf-8")

    venv_dir = repo_dir / ".venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text("home = /tmp\n", encoding="utf-8")

    pycache_dir = repo_dir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "app.cpython-314.pyc").write_bytes(b"binary")

    pytest_cache = repo_dir / ".pytest_cache"
    pytest_cache.mkdir()
    (pytest_cache / "README.md").write_text("cache", encoding="utf-8")

    build_dir = repo_dir / "build"
    build_dir.mkdir()
    (build_dir / "artifact.txt").write_text("built", encoding="utf-8")

    agent = GitHubRepoAgent()
    structure = agent.summarize_structure(repo_dir)

    assert "`app.py`" in structure
    assert "`.python-version`" not in structure
    assert "`.venv/pyvenv.cfg`" not in structure
    assert "`__pycache__/app.cpython-314.pyc`" not in structure
    assert "`.pytest_cache/README.md`" not in structure
    assert "`build/artifact.txt`" not in structure


def test_parse_owner_repo_rejects_non_github_url() -> None:
    agent = GitHubRepoAgent()

    try:
        agent.parse_owner_repo("https://example.com/not-github")
    except ValueError as exc:
        assert "Not a GitHub URL" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
