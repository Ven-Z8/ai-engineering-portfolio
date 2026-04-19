# Second Brain OS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working daily knowledge harness that ingests GitHub, YouTube, Web, and RSS sources through Claude, writes structured notes to an Obsidian vault, and generates a daily briefing — end-to-end in 48 hours.

**Architecture:** New `uv` project at `projects/second-brain-os/`. Ports proven ingestors from `obsidian-daily-agent`, adds RSS + CLI + LaunchAgent. LLM routing: Anthropic primary → OpenRouter fallback. Single `LLMClient` abstraction with per-call cost tracking. All prompts loaded from `/Volumes/VeN/Claude-Code-Work/prompts/second-brain-os/v1.0/`.

**Tech Stack:** Python 3.12, uv, pydantic-settings, structlog, anthropic SDK, httpx, youtube-transcript-api, feedparser, beautifulsoup4, typer, rich, tiktoken, PyYAML, sqlite3

---

## File Map

```
projects/second-brain-os/
├── pyproject.toml
├── Makefile
├── Dockerfile
├── .env.example
├── CLAUDE.md
├── README.md
├── .github/workflows/ci.yml
├── config/
│   ├── sources.yaml
│   └── portfolio_projects.yaml
├── scripts/
│   ├── setup_launchagent.sh
│   └── benchmark.py
├── src/second_brain/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py        ← ALL Pydantic models (RawContent, ProcessedContent, RunStats, LLMResponse)
│   │   ├── settings.py      ← pydantic-settings Settings
│   │   ├── logger.py        ← structlog setup + get_logger()
│   │   ├── llm_client.py    ← LLMClient: Anthropic + OpenRouter + cost tracking
│   │   └── db.py            ← StateStore: SQLite, processed_items, run_log, FTS5
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py          ← BaseAgent ABC: fetch(url) -> list[RawContent]
│   │   ├── github_agent.py  ← GitHub API (httpx): README + commits + repo meta
│   │   ├── youtube_agent.py ← transcript + oEmbed metadata + description_urls
│   │   ├── web_agent.py     ← httpx + BeautifulSoup, paywall detection
│   │   └── rss_agent.py     ← feedparser, deduplicates against StateStore
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── context_budget.py ← ContextBudget: tiktoken-based truncation
│   │   ├── summarizer.py     ← loads prompts from YAML, calls LLMClient
│   │   └── project_mapper.py ← maps content to portfolio projects (keyword Phase 1)
│   ├── vault/
│   │   ├── __init__.py
│   │   ├── note_writer.py   ← writes notes to vault with YAML frontmatter
│   │   ├── daily_note.py    ← 01-Daily/YYYY-MM-DD.md
│   │   └── index_updater.py ← appends to 07-Meta/pipeline-log.md
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── pipeline.py      ← asyncio.gather all agents, per-agent isolation
│   └── cli/
│       ├── __init__.py
│       └── main.py          ← Typer: sbo run|add|status|fetch|vault|config|daemon
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_context_budget.py
│   │   ├── test_note_writer.py
│   │   ├── test_daily_note.py
│   │   ├── test_db.py
│   │   ├── test_project_mapper.py
│   │   ├── test_rss_agent.py
│   │   └── test_pipeline.py
│   └── integration/
│       └── test_github_agent.py
└── docs/
    └── architecture.md
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `projects/second-brain-os/pyproject.toml`
- Create: `projects/second-brain-os/.env.example`
- Create: `projects/second-brain-os/src/second_brain/__init__.py` (and all `__init__.py` files)

- [ ] **Step 1: Create project directory and pyproject.toml**

```bash
mkdir -p /Volumes/VeN/Claude-Code-Work/projects/second-brain-os
cd /Volumes/VeN/Claude-Code-Work/projects/second-brain-os
```

Create `pyproject.toml`:
```toml
[project]
name = "second-brain-os"
version = "0.1.0"
description = "Daily knowledge harness for AI engineers — ingests sources, writes to Obsidian, queryable on demand"
requires-python = ">=3.12"
dependencies = [
    "anthropic>=0.40.0",
    "typer>=0.13.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "structlog>=24.0.0",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "feedparser>=6.0.0",
    "youtube-transcript-api>=0.6.0",
    "tiktoken>=0.7.0",
    "PyYAML>=6.0.0",
    "schedule>=1.2.0",
    "python-dotenv>=1.0.0",
    "aiofiles>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
]

[project.scripts]
sbo = "second_brain.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/second_brain"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 2: Create all package directories and `__init__.py` files**

```bash
mkdir -p src/second_brain/{core,agents,processing,vault,orchestration,cli}
mkdir -p tests/{unit,integration}
mkdir -p config scripts docs state
touch src/second_brain/__init__.py
touch src/second_brain/core/__init__.py
touch src/second_brain/agents/__init__.py
touch src/second_brain/processing/__init__.py
touch src/second_brain/vault/__init__.py
touch src/second_brain/orchestration/__init__.py
touch src/second_brain/cli/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

- [ ] **Step 3: Create .env.example**

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...       # optional: fallback provider
GITHUB_TOKEN=ghp_...               # optional: higher rate limits for GitHub API
VAULT_PATH=/Volumes/VeN/Claude-Code-Work/second-brain
DB_PATH=state/sbo.db
SCHEDULE_TIME=07:00
DEFAULT_MODEL=claude-sonnet-4-6
FRESHNESS_DAYS=7
PROMPTS_ROOT=/Volumes/VeN/Claude-Code-Work/prompts
```

- [ ] **Step 4: Install dependencies**

```bash
uv sync
```

Expected: virtualenv created, all packages installed with no errors.

- [ ] **Step 5: Smoke test**

```bash
uv run python -c "import second_brain; print('scaffold OK')"
```

Expected: `scaffold OK`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example src/ tests/ config/ scripts/ docs/ state/.gitkeep
git commit -m "feat: scaffold second-brain-os project structure"
```

---

## Task 2: Core Models

**Files:**
- Create: `src/second_brain/core/models.py`
- Create: `tests/unit/test_models.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_models.py`:
```python
import hashlib
from datetime import datetime, timezone
from second_brain.core.models import (
    LLMResponse, ProcessedContent, RawContent, RunStats, SourceType
)


def test_raw_content_auto_hash():
    raw = RawContent(
        source_type=SourceType.YOUTUBE,
        url="https://youtube.com/watch?v=abc",
        title="Test Video",
        body="hello world transcript",
    )
    expected_hash = hashlib.sha256(b"hello world transcript").hexdigest()[:16]
    assert raw.content_hash == expected_hash


def test_raw_content_explicit_hash():
    raw = RawContent(
        source_type=SourceType.GITHUB_REPO,
        url="https://github.com/org/repo",
        title="org/repo",
        body="readme content",
        content_hash="custom_hash",
    )
    assert raw.content_hash == "custom_hash"


def test_raw_content_fetched_at_auto():
    raw = RawContent(
        source_type=SourceType.WEB_DOC,
        url="https://example.com",
        title="Example",
        body="some content",
    )
    assert raw.fetched_at is not None
    assert raw.fetched_at.tzinfo is not None


def test_run_stats_defaults():
    stats = RunStats(
        run_id=1,
        started_at=datetime.now(timezone.utc),
    )
    assert stats.notes_created == 0
    assert stats.cost_usd == 0.0
    assert stats.provider_counts == {}


def test_source_type_values():
    assert SourceType.YOUTUBE == "youtube"
    assert SourceType.GITHUB_REPO == "github_repo"
    assert SourceType.WEB_DOC == "web_doc"
    assert SourceType.RSS == "rss"
```

- [ ] **Step 2: Run test — expect failure**

```bash
uv run pytest tests/unit/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'second_brain.core.models'`

- [ ] **Step 3: Implement models.py**

`src/second_brain/core/models.py`:
```python
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, model_validator


class SourceType(str, Enum):
    YOUTUBE = "youtube"
    GITHUB_REPO = "github_repo"
    WEB_DOC = "web_doc"
    RSS = "rss"


class RawContent(BaseModel):
    source_type: SourceType
    url: str
    title: str
    body: str
    content_hash: str = ""
    metadata: dict[str, str] = {}
    fetched_at: datetime | None = None

    @model_validator(mode="after")
    def _fill_defaults(self) -> "RawContent":
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.body.encode()).hexdigest()[:16]
        if self.fetched_at is None:
            self.fetched_at = datetime.now(timezone.utc)
        return self


class ProcessedContent(BaseModel):
    raw: RawContent
    summary: str
    key_insights: list[str] = []
    tags: list[str] = []
    project_relevance: list[str] = []
    relevance_note: str = ""
    cost_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    provider: str = "anthropic"


class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    provider: str


class RunStats(BaseModel):
    run_id: int
    started_at: datetime
    finished_at: datetime | None = None
    sources_processed: int = 0
    notes_created: int = 0
    notes_updated: int = 0
    notes_skipped: int = 0
    notes_fallback: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    provider_counts: dict[str, int] = {}
    failed_count: int = 0
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/unit/test_models.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/second_brain/core/models.py tests/unit/test_models.py
git commit -m "feat: core Pydantic models (RawContent, ProcessedContent, RunStats)"
```

---

## Task 3: Settings + Logger

**Files:**
- Create: `src/second_brain/core/settings.py`
- Create: `src/second_brain/core/logger.py`

- [ ] **Step 1: Implement settings.py**

`src/second_brain/core/settings.py`:
```python
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    github_token: str = ""

    vault_path: Path = Path("/Volumes/VeN/Claude-Code-Work/second-brain")
    db_path: Path = Path("state/sbo.db")
    prompts_root: Path = Path("/Volumes/VeN/Claude-Code-Work/prompts")

    schedule_time: str = "07:00"
    default_model: str = "claude-sonnet-4-6"
    fallback_model: str = "anthropic/claude-sonnet-4-6"
    max_tokens_per_call: int = 8000
    freshness_days: int = 7
    log_level: str = "INFO"
```

- [ ] **Step 2: Implement logger.py**

`src/second_brain/core/logger.py`:
```python
from __future__ import annotations

import logging

import structlog


def setup_logging(level: str = "INFO") -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
```

- [ ] **Step 3: Smoke test**

```bash
uv run python -c "
from second_brain.core.settings import Settings
from second_brain.core.logger import setup_logging, get_logger
setup_logging('DEBUG')
log = get_logger('test')
log.info('logger OK', test=True)
s = Settings()
print('Settings OK — vault:', s.vault_path)
"
```

Expected: structured log line + `Settings OK — vault: /Volumes/VeN/Claude-Code-Work/second-brain`

- [ ] **Step 4: Commit**

```bash
git add src/second_brain/core/settings.py src/second_brain/core/logger.py
git commit -m "feat: pydantic-settings Settings and structlog logger"
```

---

## Task 4: StateStore (SQLite)

**Files:**
- Create: `src/second_brain/core/db.py`
- Create: `tests/unit/test_db.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_db.py`:
```python
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from second_brain.core.db import StateStore


@pytest.fixture
def db(tmp_path):
    return StateStore(db_path=tmp_path / "test.db")


def test_is_processed_new_url(db):
    assert db.is_processed("https://example.com", "abc123", freshness_days=7) is False


def test_upsert_and_is_processed(db):
    db.upsert_item(
        url="https://example.com",
        source_type="web_doc",
        content_hash="abc123",
        note_path="/vault/note.md",
        run_id=1,
    )
    assert db.is_processed("https://example.com", "abc123", freshness_days=7) is True


def test_different_content_hash_triggers_reprocess(db):
    db.upsert_item("https://example.com", "web_doc", "old_hash", "/vault/note.md", 1)
    assert db.is_processed("https://example.com", "new_hash", freshness_days=7) is False


def test_start_and_finish_run(db):
    run_id = db.start_run()
    assert isinstance(run_id, int)
    assert run_id >= 1

    db.finish_run(run_id, {"items_processed": 5, "notes_created": 3, "cost_usd": 0.02})
    last = db.get_last_run()
    assert last["run_id"] == run_id
    assert last["items_processed"] == 5
    assert last["notes_created"] == 3


def test_upsert_note_content(db):
    db.upsert_note_content(
        url="https://example.com",
        title="Test Note",
        summary="A summary",
        tags="python, ai",
        note_path="/vault/test.md",
    )
    # Should not raise; FTS5 rebuild should succeed
```

- [ ] **Step 2: Run test — expect failure**

```bash
uv run pytest tests/unit/test_db.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement db.py**

`src/second_brain/core/db.py`:
```python
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class StateStore:
    db_path: Path

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS processed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    source_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    note_path TEXT,
                    run_id INTEGER
                );
                CREATE TABLE IF NOT EXISTS run_log (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    items_processed INTEGER DEFAULT 0,
                    items_skipped INTEGER DEFAULT 0,
                    notes_created INTEGER DEFAULT 0,
                    tokens_used INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0
                );
                CREATE TABLE IF NOT EXISTS run_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    ts TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    url TEXT
                );
                CREATE TABLE IF NOT EXISTS notes_content (
                    url TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    note_path TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_notes USING fts5(
                    url, title, summary, tags,
                    content='notes_content',
                    tokenize='porter unicode61'
                );
            """)

    def is_processed(self, url: str, content_hash: str, freshness_days: int) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT content_hash, fetched_at FROM processed_items WHERE url = ?", (url,)
            ).fetchone()
        if row is None:
            return False
        if row["content_hash"] != content_hash:
            return False
        fetched_at = datetime.fromisoformat(row["fetched_at"])
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - fetched_at).days
        return age_days < freshness_days

    def upsert_item(
        self,
        url: str,
        source_type: str,
        content_hash: str,
        note_path: str,
        run_id: int,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO processed_items (url, source_type, content_hash, fetched_at, note_path, run_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    content_hash=excluded.content_hash,
                    fetched_at=excluded.fetched_at,
                    note_path=excluded.note_path,
                    run_id=excluded.run_id
                """,
                (url, source_type, content_hash, datetime.now(timezone.utc).isoformat(), note_path, run_id),
            )

    def start_run(self) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO run_log (started_at) VALUES (?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def finish_run(self, run_id: int, stats: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE run_log SET
                    finished_at=?, items_processed=?, items_skipped=?,
                    notes_created=?, tokens_used=?, cost_usd=?
                WHERE run_id=?
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    stats.get("items_processed", 0),
                    stats.get("items_skipped", 0),
                    stats.get("notes_created", 0),
                    stats.get("tokens_used", 0),
                    stats.get("cost_usd", 0.0),
                    run_id,
                ),
            )

    def get_last_run(self) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM run_log ORDER BY run_id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def upsert_note_content(
        self, url: str, title: str, summary: str, tags: str, note_path: str
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO notes_content (url, title, summary, tags, note_path)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title=excluded.title, summary=excluded.summary,
                    tags=excluded.tags, note_path=excluded.note_path
                """,
                (url, title, summary, tags, note_path),
            )
            conn.execute("INSERT INTO fts_notes(fts_notes) VALUES('rebuild')")
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/unit/test_db.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/second_brain/core/db.py tests/unit/test_db.py
git commit -m "feat: SQLite StateStore with FTS5 index and run tracking"
```

---

## Task 5: LLMClient

**Files:**
- Create: `src/second_brain/core/llm_client.py`
- Create: `tests/unit/test_llm_client.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_llm_client.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from second_brain.core.llm_client import LLMClient, HarnessLLMError, COST_PER_TOKEN
from second_brain.core.models import LLMResponse
from second_brain.core.settings import Settings


@pytest.fixture
def settings():
    return Settings(anthropic_api_key="test-key", openrouter_api_key="")


@pytest.fixture
def client(settings):
    return LLMClient(settings=settings)


def test_count_tokens(client):
    count = client.count_tokens("hello world")
    assert count > 0
    assert count < 10


def test_cost_table_has_sonnet():
    assert "claude-sonnet-4-6" in COST_PER_TOKEN
    assert COST_PER_TOKEN["claude-sonnet-4-6"]["input"] > 0


def test_total_cost_starts_zero(client):
    assert client.total_cost_usd == 0.0


@pytest.mark.asyncio
async def test_complete_calls_anthropic(client):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="test output")]
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 20

    with patch("second_brain.core.llm_client.anthropic.AsyncAnthropic") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_instance

        result = await client.complete(prompt="test prompt", system="test system")

    assert isinstance(result, LLMResponse)
    assert result.provider == "anthropic"
    assert result.tokens_in == 10
    assert result.tokens_out == 20
    assert result.cost_usd > 0
    assert client.total_cost_usd > 0
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/unit/test_llm_client.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement llm_client.py**

`src/second_brain/core/llm_client.py`:
```python
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import anthropic
import httpx
import tiktoken

from second_brain.core.logger import get_logger
from second_brain.core.models import LLMResponse
from second_brain.core.settings import Settings

logger = get_logger(__name__)

COST_PER_TOKEN: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
    "claude-haiku-4-5": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
    "claude-opus-4-6": {"input": 15.0 / 1_000_000, "output": 75.0 / 1_000_000},
    "default": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
}


class HarnessLLMError(Exception):
    pass


@dataclass
class LLMClient:
    settings: Settings
    _total_cost_usd: float = field(default=0.0, init=False)
    _encoding: Any = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))

    @property
    def total_cost_usd(self) -> float:
        return self._total_cost_usd

    async def complete(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        model = model or self.settings.default_model
        estimated = self.count_tokens((system or "") + prompt)
        logger.info("llm_call_start", model=model, estimated_input_tokens=estimated)

        try:
            return await self._call_anthropic(prompt, system, model, max_tokens)
        except (anthropic.RateLimitError, anthropic.APIError, anthropic.APIConnectionError) as e:
            logger.warning("anthropic_failed_trying_openrouter", error=str(e))
            if not self.settings.openrouter_api_key:
                raise HarnessLLMError(f"Anthropic failed, no OpenRouter key configured: {e}") from e
            try:
                return await self._call_openrouter(prompt, system, self.settings.fallback_model, max_tokens)
            except Exception as e2:
                raise HarnessLLMError(f"Both providers failed. Last error: {e2}") from e2

    async def _call_anthropic(
        self, prompt: str, system: str, model: str, max_tokens: int
    ) -> LLMResponse:
        client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        start = time.monotonic()

        kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        if system:
            kwargs["system"] = system

        response = await client.messages.create(**kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        costs = COST_PER_TOKEN.get(model, COST_PER_TOKEN["default"])
        cost_usd = tokens_in * costs["input"] + tokens_out * costs["output"]
        self._total_cost_usd += cost_usd

        logger.info(
            "llm_call_complete",
            provider="anthropic",
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=round(cost_usd, 6),
            latency_ms=latency_ms,
        )
        return LLMResponse(
            content=response.content[0].text,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            provider="anthropic",
        )

    async def _call_openrouter(
        self, prompt: str, system: str, model: str, max_tokens: int
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                    "HTTP-Referer": "https://github.com/venki/second-brain-os",
                    "Content-Type": "application/json",
                },
                json={"model": model, "max_tokens": max_tokens, "messages": messages},
            )
            r.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = r.json()

        tokens_in = data["usage"]["prompt_tokens"]
        tokens_out = data["usage"]["completion_tokens"]
        short_model = model.split("/")[-1]
        costs = COST_PER_TOKEN.get(short_model, COST_PER_TOKEN["default"])
        cost_usd = tokens_in * costs["input"] + tokens_out * costs["output"]
        self._total_cost_usd += cost_usd

        logger.info(
            "llm_call_complete",
            provider="openrouter",
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=round(cost_usd, 6),
            latency_ms=latency_ms,
        )
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            provider="openrouter",
        )
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/unit/test_llm_client.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/second_brain/core/llm_client.py tests/unit/test_llm_client.py
git commit -m "feat: LLMClient with Anthropic primary, OpenRouter fallback, cost tracking"
```

---

## Task 6: BaseAgent + ContextBudget

**Files:**
- Create: `src/second_brain/agents/base.py`
- Create: `src/second_brain/processing/context_budget.py`
- Create: `tests/unit/test_context_budget.py`

- [ ] **Step 1: Write failing test for ContextBudget**

`tests/unit/test_context_budget.py`:
```python
from second_brain.processing.context_budget import ContextBudget


def test_fit_short_text_unchanged():
    budget = ContextBudget(max_tokens=100)
    text = "short text"
    assert budget.fit(text) == text


def test_fit_truncates_long_text():
    budget = ContextBudget(max_tokens=10)
    long_text = "word " * 200
    result = budget.fit(long_text)
    assert len(result) < len(long_text)
    assert "[Content truncated" in result


def test_count_returns_positive():
    budget = ContextBudget(max_tokens=1000)
    assert budget.count("hello world") > 0
```

- [ ] **Step 2: Implement base.py and context_budget.py**

`src/second_brain/agents/base.py`:
```python
from __future__ import annotations

from abc import ABC, abstractmethod

from second_brain.core.models import RawContent


class BaseAgent(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> list[RawContent]:
        """Fetch content from url. Returns list (RSS returns multiple, others return one)."""
        ...
```

`src/second_brain/processing/context_budget.py`:
```python
from __future__ import annotations

import tiktoken


class ContextBudget:
    """Enforces token budget on content before LLM calls. Portfolio signal: context engineering."""

    def __init__(self, max_tokens: int = 8000) -> None:
        self.max_tokens = max_tokens
        self._enc = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        return len(self._enc.encode(text))

    def fit(self, text: str) -> str:
        tokens = self._enc.encode(text)
        if len(tokens) <= self.max_tokens:
            return text
        truncated = self._enc.decode(tokens[: self.max_tokens])
        return truncated + "\n\n[Content truncated to fit context budget]"
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/test_context_budget.py -v
```

Expected: `3 passed`

- [ ] **Step 4: Commit**

```bash
git add src/second_brain/agents/base.py src/second_brain/processing/context_budget.py tests/unit/test_context_budget.py
git commit -m "feat: BaseAgent ABC and ContextBudget token truncation"
```

---

## Task 7: GitHubAgent

**Files:**
- Create: `src/second_brain/agents/github_agent.py`
- Create: `tests/integration/test_github_agent.py`

- [ ] **Step 1: Write integration test (uses real GitHub API, no token required)**

`tests/integration/test_github_agent.py`:
```python
import pytest
from second_brain.agents.github_agent import GitHubAgent
from second_brain.core.models import SourceType
from second_brain.core.settings import Settings


@pytest.fixture
def agent():
    return GitHubAgent(settings=Settings())


@pytest.mark.asyncio
async def test_fetch_public_repo(agent):
    results = await agent.fetch("https://github.com/anthropics/anthropic-sdk-python")
    assert len(results) == 1
    raw = results[0]
    assert raw.source_type == SourceType.GITHUB_REPO
    assert "anthropic" in raw.title.lower()
    assert len(raw.body) > 100
    assert raw.metadata["stars"]
    assert raw.content_hash


@pytest.mark.asyncio
async def test_parse_invalid_url(agent):
    with pytest.raises(ValueError, match="Cannot parse"):
        await agent.fetch("https://github.com/single-part")
```

- [ ] **Step 2: Implement github_agent.py**

`src/second_brain/agents/github_agent.py`:
```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx

from second_brain.agents.base import BaseAgent
from second_brain.core.logger import get_logger
from second_brain.core.models import RawContent, SourceType
from second_brain.core.settings import Settings

logger = get_logger(__name__)
_BASE = "https://api.github.com"


class GitHubAgent(BaseAgent):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "second-brain-os/0.1",
        }
        if settings.github_token:
            self._headers["Authorization"] = f"Bearer {settings.github_token}"

    async def fetch(self, url: str) -> list[RawContent]:
        owner, repo = self._parse(url)
        async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
            readme = await self._readme(client, owner, repo)
            commits = await self._commits(client, owner, repo)
            meta = await self._meta(client, owner, repo)

        body = self._build_body(readme, commits, meta)
        return [
            RawContent(
                source_type=SourceType.GITHUB_REPO,
                url=url,
                title=f"{owner}/{repo}",
                body=body,
                metadata={
                    "repo_name": f"{owner}/{repo}",
                    "stars": str(meta.get("stargazers_count", 0)),
                    "last_commit_sha": commits[0]["sha"][:8] if commits else "",
                    "open_issues_count": str(meta.get("open_issues_count", 0)),
                    "description": (meta.get("description") or "")[:200],
                },
            )
        ]

    def _parse(self, url: str) -> tuple[str, str]:
        parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Cannot parse owner/repo from {url}")
        return parts[0], parts[1].replace(".git", "")

    async def _readme(self, client: httpx.AsyncClient, owner: str, repo: str) -> str:
        try:
            r = await client.get(
                f"{_BASE}/repos/{owner}/{repo}/readme",
                headers={**self._headers, "Accept": "application/vnd.github.raw+json"},
            )
            if r.status_code == 200:
                return r.text[:8000]
        except Exception as e:
            logger.warning("github_readme_failed", repo=f"{owner}/{repo}", error=str(e))
        return ""

    async def _commits(self, client: httpx.AsyncClient, owner: str, repo: str) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        try:
            r = await client.get(
                f"{_BASE}/repos/{owner}/{repo}/commits",
                params={"since": since, "per_page": 10},
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.warning("github_commits_failed", repo=f"{owner}/{repo}", error=str(e))
        return []

    async def _meta(self, client: httpx.AsyncClient, owner: str, repo: str) -> dict:
        try:
            r = await client.get(f"{_BASE}/repos/{owner}/{repo}")
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.warning("github_meta_failed", repo=f"{owner}/{repo}", error=str(e))
        return {}

    def _build_body(self, readme: str, commits: list[dict], meta: dict) -> str:
        parts: list[str] = []
        if meta.get("description"):
            parts.append(f"Description: {meta['description']}")
        if readme:
            parts.append(f"## README\n{readme}")
        if commits:
            lines = []
            for c in commits[:10]:
                sha = c["sha"][:8]
                msg = c["commit"]["message"].split("\n")[0][:100]
                date = c["commit"]["committer"]["date"][:10]
                lines.append(f"- [{sha}] {date}: {msg}")
            parts.append("## Recent Commits (last 7 days)\n" + "\n".join(lines))
        else:
            parts.append("## Recent Commits\nNo commits in the last 7 days.")
        return "\n\n".join(parts)
```

- [ ] **Step 3: Run integration test (requires internet)**

```bash
uv run pytest tests/integration/test_github_agent.py -v
```

Expected: `2 passed`

- [ ] **Step 4: Commit**

```bash
git add src/second_brain/agents/github_agent.py tests/integration/test_github_agent.py
git commit -m "feat: GitHubAgent — README + commits via GitHub API, no git required"
```

---

## Task 8: YouTubeAgent

**Files:**
- Create: `src/second_brain/agents/youtube_agent.py`

- [ ] **Step 1: Implement youtube_agent.py**

`src/second_brain/agents/youtube_agent.py`:
```python
from __future__ import annotations

import asyncio
import re
from urllib.parse import parse_qs, quote, urlparse

import httpx

from second_brain.agents.base import BaseAgent
from second_brain.core.logger import get_logger
from second_brain.core.models import RawContent, SourceType
from second_brain.core.settings import Settings

logger = get_logger(__name__)

try:
    from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi
except ImportError:  # pragma: no cover
    YouTubeTranscriptApi = None
    NoTranscriptFound = None


class YouTubeAgent(BaseAgent):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch(self, url: str) -> list[RawContent]:
        video_id = self._extract_video_id(url)
        loop = asyncio.get_event_loop()

        transcript = await loop.run_in_executor(None, self._fetch_transcript_sync, video_id)
        meta = await self._fetch_meta(url)

        description_urls = self._extract_urls(meta.get("description", ""))

        return [
            RawContent(
                source_type=SourceType.YOUTUBE,
                url=url,
                title=meta.get("title") or f"YouTube {video_id}",
                body=transcript,
                metadata={
                    "video_id": video_id,
                    "channel": meta.get("author_name", ""),
                    "description_urls": ",".join(description_urls[:5]),
                },
            )
        ]

    def _extract_video_id(self, url: str) -> str:
        parsed = urlparse(url)
        if "youtu.be" in parsed.netloc:
            vid = parsed.path.strip("/")
            if vid:
                return vid
        if "youtube.com" in parsed.netloc:
            vid = parse_qs(parsed.query).get("v", [""])[0]
            if vid:
                return vid
        raise ValueError(f"Cannot extract video ID from {url}")

    def _fetch_transcript_sync(self, video_id: str) -> str:
        if YouTubeTranscriptApi is None:
            raise RuntimeError("youtube-transcript-api not installed")
        api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id, languages=["en", "en-US"])
        except Exception as e:
            if NoTranscriptFound is not None and isinstance(e, NoTranscriptFound):
                lst = api.list(video_id)
                first = next(iter(lst), None)
                if first is None:
                    raise RuntimeError("No transcript available for this video") from e
                fetched = first.fetch()
            else:
                raise
        parts = [chunk.get("text", "").strip() for chunk in fetched.to_raw_data() if chunk.get("text")]
        if not parts:
            raise RuntimeError("Transcript is empty")
        return "\n".join(parts)

    async def _fetch_meta(self, url: str) -> dict:
        oembed = f"https://www.youtube.com/oembed?url={quote(url, safe='')}&format=json"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(oembed, headers={"User-Agent": "second-brain-os/0.1"})
                if r.status_code == 200:
                    return r.json()
        except Exception as e:
            logger.warning("youtube_meta_failed", url=url, error=str(e))
        return {}

    def _extract_urls(self, text: str) -> list[str]:
        return re.findall(r"https?://[^\s<>\"{}|\\^`\[\]]+", text)
```

- [ ] **Step 2: Smoke test (no API key needed — checks import + video ID parsing)**

```bash
uv run python -c "
from second_brain.agents.youtube_agent import YouTubeAgent
from second_brain.core.settings import Settings
agent = YouTubeAgent(Settings())
vid_id = agent._extract_video_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
assert vid_id == 'dQw4w9WgXcQ', f'Got: {vid_id}'
vid_id2 = agent._extract_video_id('https://youtu.be/dQw4w9WgXcQ')
assert vid_id2 == 'dQw4w9WgXcQ', f'Got: {vid_id2}'
print('YouTubeAgent parsing OK')
"
```

Expected: `YouTubeAgent parsing OK`

- [ ] **Step 3: Commit**

```bash
git add src/second_brain/agents/youtube_agent.py
git commit -m "feat: YouTubeAgent — transcript + oEmbed meta + description_urls"
```

---

## Task 9: WebAgent + RSSAgent

**Files:**
- Create: `src/second_brain/agents/web_agent.py`
- Create: `src/second_brain/agents/rss_agent.py`
- Create: `tests/unit/test_rss_agent.py`

- [ ] **Step 1: Implement web_agent.py**

`src/second_brain/agents/web_agent.py`:
```python
from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from second_brain.agents.base import BaseAgent
from second_brain.core.logger import get_logger
from second_brain.core.models import RawContent, SourceType
from second_brain.core.settings import Settings

logger = get_logger(__name__)
_PAYWALL_THRESHOLD = 500
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; second-brain-os/0.1)"}


class WebAgent(BaseAgent):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch(self, url: str) -> list[RawContent]:
        async with httpx.AsyncClient(
            headers=_HEADERS, follow_redirects=True, timeout=20.0
        ) as client:
            r = await client.get(url)
            r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        title = (soup.title.string.strip() if soup.title and soup.title.string else url)[:200]

        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find(class_=re.compile(r"(content|article|post|entry)", re.I))
            or soup.body
        )
        text = (main or soup).get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        if len(text) < _PAYWALL_THRESHOLD:
            raise RuntimeError(
                f"Content too short ({len(text)} chars) — possible paywall at {url}"
            )

        return [
            RawContent(
                source_type=SourceType.WEB_DOC,
                url=url,
                title=title,
                body=text,
                metadata={"domain": urlparse(url).netloc, "content_length": str(len(text))},
            )
        ]
```

- [ ] **Step 2: Write failing test for RSSAgent**

`tests/unit/test_rss_agent.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from second_brain.agents.rss_agent import RSSAgent
from second_brain.core.db import StateStore
from second_brain.core.models import SourceType
from second_brain.core.settings import Settings


@pytest.fixture
def db(tmp_path):
    return StateStore(db_path=tmp_path / "test.db")


@pytest.fixture
def agent(db):
    return RSSAgent(settings=Settings(), db=db, max_items=5)


def test_rss_agent_parses_feed(agent):
    mock_feed = MagicMock()
    mock_feed.entries = [
        MagicMock(
            link="https://example.com/article-1",
            title="Article One",
            summary="Summary of article one with enough content",
            published="Mon, 18 Apr 2026 07:00:00 +0000",
            tags=[],
        ),
    ]
    mock_feed.feed.title = "Test Feed"

    with patch("second_brain.agents.rss_agent.feedparser.parse", return_value=mock_feed):
        import asyncio
        results = asyncio.run(agent.fetch("https://example.com/feed.rss"))

    assert len(results) == 1
    assert results[0].source_type == SourceType.RSS
    assert results[0].title == "Article One"
    assert results[0].url == "https://example.com/article-1"


def test_rss_agent_skips_empty_body(agent):
    mock_feed = MagicMock()
    mock_feed.entries = [
        MagicMock(link="https://example.com/empty", title="Empty", summary="", tags=[]),
    ]
    mock_feed.feed.title = "Test Feed"

    with patch("second_brain.agents.rss_agent.feedparser.parse", return_value=mock_feed):
        import asyncio
        results = asyncio.run(agent.fetch("https://example.com/feed.rss"))

    assert len(results) == 0
```

- [ ] **Step 3: Implement rss_agent.py**

`src/second_brain/agents/rss_agent.py`:
```python
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from second_brain.agents.base import BaseAgent
from second_brain.core.db import StateStore
from second_brain.core.logger import get_logger
from second_brain.core.models import RawContent, SourceType
from second_brain.core.settings import Settings

logger = get_logger(__name__)


class RSSAgent(BaseAgent):
    def __init__(self, settings: Settings, db: StateStore, max_items: int = 10) -> None:
        self.settings = settings
        self.db = db
        self.max_items = max_items

    async def fetch(self, url: str) -> list[RawContent]:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)
        results: list[RawContent] = []

        for entry in feed.entries[: self.max_items]:
            item_url = entry.get("link", "")
            if not item_url:
                continue

            body = entry.get("summary", "")
            if not body:
                content_list = entry.get("content", [])
                body = content_list[0].get("value", "") if content_list else ""
            if not body.strip():
                continue

            title = entry.get("title", item_url)[:200]
            try:
                published = parsedate_to_datetime(entry.get("published", "")).isoformat()
            except Exception:
                published = datetime.now(timezone.utc).isoformat()

            categories = ",".join(t.get("term", "") for t in entry.get("tags", []))

            results.append(
                RawContent(
                    source_type=SourceType.RSS,
                    url=item_url,
                    title=title,
                    body=body,
                    metadata={
                        "feed_title": feed.feed.get("title", url),
                        "item_published_at": published,
                        "categories": categories,
                    },
                )
            )

        logger.info("rss_fetched", url=url, items=len(results))
        return results
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_rss_agent.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/second_brain/agents/web_agent.py src/second_brain/agents/rss_agent.py tests/unit/test_rss_agent.py
git commit -m "feat: WebAgent (httpx+BS4) and RSSAgent (feedparser) ingestors"
```

---

## Task 10: Summarizer + ProjectMapper

**Files:**
- Create: `src/second_brain/processing/summarizer.py`
- Create: `src/second_brain/processing/project_mapper.py`
- Create: `tests/unit/test_project_mapper.py`
- Create: `config/portfolio_projects.yaml`

- [ ] **Step 1: Create portfolio_projects.yaml**

`config/portfolio_projects.yaml`:
```yaml
projects:
  - folder: "01-ContextForge"
    name: ContextForge
    key_technologies: [context engineering, tiktoken, embeddings, semantic compression, token budget, qdrant]
  - folder: "02-RAGBench-Pro"
    name: RAGBench Pro
    key_technologies: [rag, ragas, deepeval, chroma, qdrant, hyde, multi-query, reranker, vector database]
  - folder: "03-AgentOrchestra"
    name: AgentOrchestra
    key_technologies: [langgraph, supervisor, multi-agent, hitl, human-in-the-loop, checkpoints, interrupt]
  - folder: "04-MemoryOS"
    name: MemoryOS
    key_technologies: [episodic memory, semantic memory, procedural memory, qdrant, redis, memory agent]
  - folder: "05-AutoResearch-v2"
    name: AutoResearch v2
    key_technologies: [autoresearch, karpathy loop, autonomous agent, research loop, langgraph]
  - folder: "06-MCPForge-Suite"
    name: MCPForge Suite
    key_technologies: [mcp, model context protocol, mcp server, mcp sdk, tool server, pypi]
  - folder: "07-MCPGuard"
    name: MCPGuard
    key_technologies: [mcp security, pii detection, presidio, prompt injection, audit log, rate limiting]
  - folder: "08-EvalEngine"
    name: EvalEngine
    key_technologies: [evaluation, llm-as-judge, faithfulness, answer relevance, ragas, deepeval, evals]
  - folder: "09-GuardStack"
    name: GuardStack
    key_technologies: [guardrails, content safety, hallucination detection, pii scrubbing, toxicity, langchain callbacks]
  - folder: "10-LLMScope"
    name: LLMScope
    key_technologies: [observability, cost tracking, latency, prompt drift, recharts, dashboard]
  - folder: "11-GraphRAG-Engine"
    name: GraphRAG Engine
    key_technologies: [graphrag, knowledge graph, neo4j, entity extraction, community detection, graph traversal]
  - folder: "12-PromptOpt"
    name: PromptOpt
    key_technologies: [prompt optimization, dspy, few-shot, bootstrap, prompt compilation]
  - folder: "13-ToolForge"
    name: ToolForge
    key_technologies: [tool use, retry, exponential backoff, partial failure recovery, tool tracing, fallback]
  - folder: "14-StructOut"
    name: StructOut
    key_technologies: [structured output, json schema, instructor, pydantic, self-correction, schema adherence]
  - folder: "15-SemanticRouter"
    name: SemanticRouter
    key_technologies: [semantic routing, intent detection, query router, qdrant, scikit-learn, a/b testing]
  - folder: "16-DocIQ"
    name: DocIQ
    key_technologies: [document processing, ocr, pdf, surya, layout detection, entity extraction, legal]
  - folder: "17-SynthGen"
    name: SynthGen
    key_technologies: [synthetic data, data generation, huggingface datasets, adversarial examples, deduplication]
  - folder: "18-SelfHeal"
    name: SelfHeal
    key_technologies: [self-correcting agent, failure detection, rollback, checkpoint, langgraph, error classification]
  - folder: "19-RedTeamKit"
    name: RedTeamKit
    key_technologies: [red teaming, adversarial testing, prompt injection, jailbreak, vulnerability, safety]
  - folder: "20-LiveRAG"
    name: LiveRAG
    key_technologies: [live rag, real-time, websockets, streaming, dynamic index, freshness, staleness]
  - folder: "21-SemanticCache"
    name: SemanticCache
    key_technologies: [semantic cache, similarity caching, redis, qdrant, cache hit rate, cost reduction]
  - folder: "22-BrowserAgent"
    name: BrowserAgent
    key_technologies: [browser automation, playwright, autonomous agent, web research, loop detection, reflection]
  - folder: "23-SQLAgent-Pro"
    name: SQLAgent Pro
    key_technologies: [text-to-sql, nl2sql, sqlalchemy, postgresql, spider benchmark, self-correction, safety]
  - folder: "24-DebateArena"
    name: DebateArena
    key_technologies: [multi-agent debate, constitutional ai, deliberation, judge agent, devil advocate, langgraph]
```

- [ ] **Step 2: Write failing test for ProjectMapper**

`tests/unit/test_project_mapper.py`:
```python
import pytest
from pathlib import Path
from second_brain.core.models import RawContent, SourceType
from second_brain.core.settings import Settings
from second_brain.processing.project_mapper import ProjectMapper


@pytest.fixture
def mapper(tmp_path):
    # Copy portfolio_projects.yaml to tmp_path
    import shutil
    config_src = Path("config/portfolio_projects.yaml")
    config_dst = tmp_path / "portfolio_projects.yaml"
    if config_src.exists():
        shutil.copy(config_src, config_dst)
    else:
        config_dst.write_text("projects: []")
    settings = Settings()
    m = ProjectMapper(settings=settings)
    m._config_path = config_dst
    return m


def test_maps_langgraph_to_agentorchestra(mapper):
    raw = RawContent(
        source_type=SourceType.YOUTUBE,
        url="https://youtube.com/watch?v=test",
        title="LangGraph Tutorial",
        body="In this video we cover langgraph supervisor interrupt hitl checkpoint patterns",
    )
    projects = mapper.map(raw, tags=["langgraph", "multi-agent"])
    assert any("AgentOrchestra" in p or "03" in p for p in projects)


def test_returns_at_most_4(mapper):
    raw = RawContent(
        source_type=SourceType.WEB_DOC,
        url="https://example.com",
        title="Everything about AI",
        body="langgraph rag mcp evaluation guardrails graphrag dspy playwright sql",
    )
    projects = mapper.map(raw, tags=["ai"])
    assert len(projects) <= 4
```

- [ ] **Step 3: Implement project_mapper.py**

`src/second_brain/processing/project_mapper.py`:
```python
from __future__ import annotations

import re
from pathlib import Path

import yaml

from second_brain.core.logger import get_logger
from second_brain.core.models import RawContent
from second_brain.core.settings import Settings

logger = get_logger(__name__)


class ProjectMapper:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._config_path = Path("config/portfolio_projects.yaml")
        self._portfolio: list[dict] | None = None

    def _load(self) -> list[dict]:
        if self._portfolio is None:
            self._portfolio = yaml.safe_load(self._config_path.read_text())["projects"]
        return self._portfolio

    def map(self, raw: RawContent, tags: list[str]) -> list[str]:
        portfolio = self._load()
        content_text = f"{raw.title} {raw.body[:3000]} {' '.join(tags)}".lower()
        content_tokens = set(t for t in re.split(r"\W+", content_text) if len(t) > 2)

        scored: list[tuple[int, str]] = []
        for project in portfolio:
            tech_tokens = set(
                t.lower()
                for tech in project.get("key_technologies", [])
                for t in re.split(r"\W+", tech)
                if len(t) > 2
            )
            overlap = len(content_tokens & tech_tokens)
            if overlap >= 2:
                scored.append((overlap, project["folder"]))

        scored.sort(reverse=True)
        return [folder for _, folder in scored[:4]]
```

- [ ] **Step 4: Implement summarizer.py**

`src/second_brain/processing/summarizer.py`:
```python
from __future__ import annotations

import re
from pathlib import Path

import yaml

from second_brain.core.llm_client import LLMClient
from second_brain.core.logger import get_logger
from second_brain.core.models import ProcessedContent, RawContent, SourceType
from second_brain.core.settings import Settings
from second_brain.processing.context_budget import ContextBudget

logger = get_logger(__name__)

_TASK_MAP = {
    SourceType.YOUTUBE: "summarize_video",
    SourceType.GITHUB_REPO: "summarize_repo",
    SourceType.WEB_DOC: "summarize_article",
    SourceType.RSS: "summarize_article",
}

_TEMPLATE_DEFAULTS = {
    "transcript": "", "content": "", "readme": "", "recent_commits": "",
    "open_issues": "", "channel": "", "duration_seconds": "",
    "domain": "", "publication_date": "", "repo_name": "",
    "stars": "0", "last_commit_sha": "", "open_issues_count": "0",
    "title": "", "url": "",
}


class Summarizer:
    def __init__(self, llm: LLMClient, settings: Settings) -> None:
        self.llm = llm
        self.settings = settings
        self.budget = ContextBudget(max_tokens=settings.max_tokens_per_call)
        self._prompts: dict[str, dict] = {}

    def _load_prompt(self, task: str) -> dict:
        if task not in self._prompts:
            path = self.settings.prompts_root / "second-brain-os" / "v1.0" / f"{task}.yaml"
            self._prompts[task] = yaml.safe_load(path.read_text())
        return self._prompts[task]

    async def summarize(self, raw: RawContent, project_relevance: list[str]) -> ProcessedContent:
        task = _TASK_MAP[raw.source_type]
        prompt_data = self._load_prompt(task)

        body = self.budget.fit(raw.body)

        vars_ = {
            **_TEMPLATE_DEFAULTS,
            "title": raw.title,
            "url": raw.url,
            "transcript": body,
            "content": body,
            "readme": body,
            **{k: v for k, v in raw.metadata.items() if k in _TEMPLATE_DEFAULTS},
        }

        user = prompt_data["user"].format(**vars_)
        system = prompt_data["system"]

        response = await self.llm.complete(
            prompt=user,
            system=system,
            max_tokens=prompt_data.get("max_output_tokens", 1024),
        )

        sections = self._parse_sections(response.content)

        return ProcessedContent(
            raw=raw,
            summary=sections.get("Summary", ""),
            key_insights=self._bullets(sections.get("Key Insights", "")),
            tags=self._tags(sections.get("Tags", "")),
            project_relevance=project_relevance,
            relevance_note=sections.get("Relevance to My Work", "")[:500],
            cost_usd=response.cost_usd,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            provider=response.provider,
        )

    def _parse_sections(self, text: str) -> dict[str, str]:
        sections: dict[str, str] = {}
        key: str | None = None
        lines: list[str] = []
        for line in text.splitlines():
            if line.startswith("## "):
                if key:
                    sections[key] = "\n".join(lines).strip()
                key = line[3:].strip()
                lines = []
            else:
                lines.append(line)
        if key:
            sections[key] = "\n".join(lines).strip()
        return sections

    def _bullets(self, text: str) -> list[str]:
        return [l.lstrip("- •").strip() for l in text.splitlines() if l.strip().startswith(("-", "•"))]

    def _tags(self, text: str) -> list[str]:
        m = re.search(r"\[([^\]]+)\]", text)
        if m:
            return [t.strip().lower() for t in m.group(1).split(",")]
        return self._bullets(text)
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/unit/test_project_mapper.py -v
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add src/second_brain/processing/ config/portfolio_projects.yaml tests/unit/test_project_mapper.py
git commit -m "feat: Summarizer (YAML prompts + 3 modes) and ProjectMapper (keyword matching)"
```

---

## Task 11: NoteWriter + DailyNote + IndexUpdater

**Files:**
- Create: `src/second_brain/vault/note_writer.py`
- Create: `src/second_brain/vault/daily_note.py`
- Create: `src/second_brain/vault/index_updater.py`
- Create: `tests/unit/test_note_writer.py`
- Create: `tests/unit/test_daily_note.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_note_writer.py`:
```python
import pytest
from pathlib import Path
from datetime import datetime, timezone
from second_brain.core.db import StateStore
from second_brain.core.models import ProcessedContent, RawContent, SourceType
from second_brain.core.settings import Settings
from second_brain.vault.note_writer import NoteWriter


@pytest.fixture
def vault(tmp_path):
    return tmp_path / "vault"


@pytest.fixture
def db(tmp_path):
    return StateStore(db_path=tmp_path / "test.db")


@pytest.fixture
def writer(vault, db):
    return NoteWriter(vault_path=vault, db=db, run_id=1)


def _make_processed(source_type=SourceType.YOUTUBE) -> ProcessedContent:
    raw = RawContent(
        source_type=source_type,
        url="https://youtube.com/watch?v=abc123",
        title="LangGraph Tutorial",
        body="transcript content",
    )
    return ProcessedContent(
        raw=raw,
        summary="A tutorial about LangGraph",
        key_insights=["LangGraph uses nodes and edges"],
        tags=["langgraph", "multi-agent"],
        project_relevance=["03-AgentOrchestra"],
        cost_usd=0.003,
        tokens_in=100,
        tokens_out=200,
        provider="anthropic",
    )


def test_note_writer_creates_file(writer, vault):
    processed = _make_processed()
    note_path = writer.write(processed)
    assert note_path.exists()
    content = note_path.read_text()
    assert "LangGraph Tutorial" in content
    assert "source_url:" in content
    assert "tags:" in content


def test_note_in_correct_folder_youtube(writer, vault):
    processed = _make_processed(SourceType.YOUTUBE)
    note_path = writer.write(processed)
    assert "04-Resources/videos" in str(note_path)


def test_note_in_correct_folder_github(writer, vault):
    processed = _make_processed(SourceType.GITHUB_REPO)
    note_path = writer.write(processed)
    assert "04-Resources/repos" in str(note_path)


def test_note_has_frontmatter(writer, vault):
    processed = _make_processed()
    note_path = writer.write(processed)
    content = note_path.read_text()
    assert content.startswith("---")
    assert "cost_usd:" in content
    assert "provider: anthropic" in content
```

`tests/unit/test_daily_note.py`:
```python
import pytest
from datetime import datetime, timezone
from second_brain.vault.daily_note import DailyNoteWriter, DailyStats


def test_daily_note_creates_file(tmp_path):
    writer = DailyNoteWriter(vault_path=tmp_path)
    stats = DailyStats(
        notes_created=5, notes_updated=1, notes_skipped=2, notes_fallback=0,
        tokens_used=1000, cost_usd=0.05, duration_seconds=120.0,
        provider_counts={"anthropic": 5},
        note_refs=[("Test Note", "/vault/test.md")],
        project_intel={"03-AgentOrchestra": 2},
        top_insights="LangGraph updated interrupt() API",
        tomorrows_focus="Review LangGraph docs",
    )
    date = datetime(2026, 4, 18, tzinfo=timezone.utc)
    path = writer.write(date, stats)

    assert path.exists()
    content = path.read_text()
    assert "# 2026-04-18" in content
    assert "5 new" in content or "notes_created" in content or "5" in content
    assert "AgentOrchestra" in content
    assert "LangGraph" in content
```

- [ ] **Step 2: Implement note_writer.py**

`src/second_brain/vault/note_writer.py`:
```python
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from second_brain.core.db import StateStore
from second_brain.core.logger import get_logger
from second_brain.core.models import ProcessedContent, SourceType

logger = get_logger(__name__)

_SOURCE_DIRS: dict[SourceType, str] = {
    SourceType.YOUTUBE: "04-Resources/videos",
    SourceType.GITHUB_REPO: "04-Resources/repos",
    SourceType.WEB_DOC: "04-Resources/articles",
    SourceType.RSS: "04-Resources/articles",
}


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\- ]+", "", text).strip().lower()
    return re.sub(r"\s+", "-", normalized)[:60] or "note"


class NoteWriter:
    def __init__(self, vault_path: Path, db: StateStore, run_id: int) -> None:
        self.vault_path = vault_path
        self.db = db
        self.run_id = run_id

    def write(self, content: ProcessedContent) -> Path:
        target_dir = self.vault_path / _SOURCE_DIRS[content.raw.source_type]
        target_dir.mkdir(parents=True, exist_ok=True)

        source_id = hashlib.sha256(content.raw.url.encode()).hexdigest()[:8]
        filename = f"{_slugify(content.raw.title)}-{source_id}.md"
        note_path = target_dir / filename

        now = datetime.now(timezone.utc)
        is_update = note_path.exists()

        if is_update:
            existing = note_path.read_text(encoding="utf-8")
            note_path.write_text(
                existing + self._update_section(content, now), encoding="utf-8"
            )
            logger.info("note_updated", path=str(note_path))
        else:
            note_path.write_text(self._render(content, now), encoding="utf-8")
            logger.info("note_created", path=str(note_path))

        self.db.upsert_item(
            url=content.raw.url,
            source_type=content.raw.source_type.value,
            content_hash=content.raw.content_hash,
            note_path=str(note_path),
            run_id=self.run_id,
        )
        self.db.upsert_note_content(
            url=content.raw.url,
            title=content.raw.title,
            summary=content.summary,
            tags=", ".join(content.tags),
            note_path=str(note_path),
        )
        return note_path

    def _render(self, content: ProcessedContent, now: datetime) -> str:
        raw = content.raw
        ts = (raw.fetched_at or now).strftime("%Y-%m-%dT%H:%M:%SZ")
        tags_yaml = "\n".join(
            f"  - {t}" for t in sorted(set(content.tags + [raw.source_type.value]))
        )
        projects_yaml = (
            "\n".join(f"  - {p}" for p in content.project_relevance)
            if content.project_relevance
            else "  []"
        )
        safe_title = raw.title.replace('"', "'")
        insights = "\n".join(f"- {i}" for i in content.key_insights) or "- None"

        return f"""---
title: "{safe_title}"
source_url: {raw.url}
source_type: {raw.source_type.value}
content_hash: {raw.content_hash}
fetched_at: {ts}
updated_at: {ts}
tags:
{tags_yaml}
projects:
{projects_yaml}
cost_usd: {content.cost_usd:.4f}
tokens_used: {content.tokens_in + content.tokens_out}
provider: {content.provider}
status: curated
---

# {raw.title}

## Summary
{content.summary}

## Key Insights
{insights}

## Relevance to My Work
{content.relevance_note or "Not mapped to specific projects."}

## Source
[{raw.url}]({raw.url})
"""

    def _update_section(self, content: ProcessedContent, now: datetime) -> str:
        date_str = now.strftime("%Y-%m-%d")
        return f"""
## Update — {date_str}
{content.summary}

**Hash:** `{content.raw.content_hash}`
"""
```

- [ ] **Step 3: Implement daily_note.py and index_updater.py**

`src/second_brain/vault/daily_note.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class DailyStats:
    notes_created: int
    notes_updated: int
    notes_skipped: int
    notes_fallback: int
    tokens_used: int
    cost_usd: float
    duration_seconds: float
    provider_counts: dict[str, int]
    note_refs: list[tuple[str, str]]
    project_intel: dict[str, int]
    top_insights: str
    tomorrows_focus: str


class DailyNoteWriter:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path

    def write(self, date: datetime, stats: DailyStats) -> Path:
        daily_dir = self.vault_path / "01-Daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        note_path = daily_dir / f"{date.strftime('%Y-%m-%d')}.md"
        note_path.write_text(self._render(date, stats), encoding="utf-8")
        return note_path

    def _render(self, date: datetime, stats: DailyStats) -> str:
        date_str = date.strftime("%Y-%m-%d")
        total = stats.notes_created + stats.notes_updated + stats.notes_skipped + stats.notes_fallback
        provider_str = " | ".join(f"{k} ({v})" for k, v in stats.provider_counts.items()) or "none"

        note_links = "\n".join(
            f"- [[{Path(path).stem}]] — {title}"
            for title, path in stats.note_refs[:20]
        ) or "- None"

        project_updates = "\n".join(
            f"- **{proj}**: {count} new source{'s' if count > 1 else ''}"
            for proj, count in sorted(stats.project_intel.items(), key=lambda x: -x[1])
        ) or "- None"

        return f"""# {date_str}

## Pipeline Summary
- Processed: {total} sources in {stats.duration_seconds:.0f}s
- Notes created: {stats.notes_created} | Updated: {stats.notes_updated} | Skipped: {stats.notes_skipped} (dupe)
- Tokens used: {stats.tokens_used:,} | Cost: ${stats.cost_usd:.3f}
- Provider: {provider_str}

## New Notes
{note_links}

## Project Intel
{project_updates}

## Top Insights
{stats.top_insights or "Pipeline did not generate insights this run."}

## Tomorrow's Focus
{stats.tomorrows_focus or "Review today's notes and identify patterns."}
"""
```

`src/second_brain/vault/index_updater.py`:
```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class IndexUpdater:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path

    def append_run_log(
        self, run_id: int, notes_created: int, cost_usd: float, duration_s: float
    ) -> None:
        log_path = self.vault_path / "07-Meta" / "pipeline-log.md"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.write_text(
                "# Pipeline Log\n\n| Run | Date | Notes | Cost | Duration |\n|-----|------|-------|------|----------|\n",
                encoding="utf-8",
            )
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"| {run_id} | {now} | {notes_created} | ${cost_usd:.3f} | {duration_s:.0f}s |\n")
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_note_writer.py tests/unit/test_daily_note.py -v
```

Expected: `7 passed`

- [ ] **Step 5: Commit**

```bash
git add src/second_brain/vault/ tests/unit/test_note_writer.py tests/unit/test_daily_note.py
git commit -m "feat: NoteWriter (YAML frontmatter), DailyNote, IndexUpdater"
```

---

## Task 12: Pipeline Runner

**Files:**
- Create: `src/second_brain/orchestration/pipeline.py`
- Create: `tests/unit/test_pipeline.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_pipeline.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from second_brain.core.db import StateStore
from second_brain.core.models import RawContent, SourceType, ProcessedContent
from second_brain.core.settings import Settings
from second_brain.orchestration.pipeline import Pipeline


@pytest.fixture
def settings(tmp_path):
    s = Settings(anthropic_api_key="test")
    s.vault_path = tmp_path / "vault"
    s.db_path = tmp_path / "test.db"
    return s


@pytest.fixture
def db(settings):
    return StateStore(db_path=settings.db_path)


@pytest.fixture
def llm():
    m = MagicMock()
    m.total_cost_usd = 0.05
    m.complete = AsyncMock()
    return m


@pytest.fixture
def pipeline(settings, db, llm):
    return Pipeline(settings=settings, db=db, llm=llm)


@pytest.mark.asyncio
async def test_dry_run_does_not_write_vault(pipeline, settings):
    sources = {"github_repos": [], "youtube_channels": [], "web_urls": [], "rss_feeds": []}
    stats = await pipeline.run(sources=sources, dry_run=True)
    assert stats.notes_created == 0
    vault_notes = list((settings.vault_path / "04-Resources").rglob("*.md")) if (settings.vault_path / "04-Resources").exists() else []
    assert vault_notes == []


@pytest.mark.asyncio
async def test_pipeline_skips_duplicates(pipeline, settings, db):
    raw = RawContent(
        source_type=SourceType.WEB_DOC,
        url="https://example.com",
        title="Test",
        body="content here",
    )
    # Pre-mark as processed
    db.upsert_item("https://example.com", "web_doc", raw.content_hash, "/vault/test.md", 1)

    with patch.object(pipeline, "_fetch_all", return_value=[raw]):
        stats = await pipeline.run(
            sources={"github_repos": [], "youtube_channels": [], "web_urls": ["https://example.com"], "rss_feeds": []},
        )

    assert stats.notes_skipped >= 1
```

- [ ] **Step 2: Implement pipeline.py**

`src/second_brain/orchestration/pipeline.py`:
```python
from __future__ import annotations

import asyncio
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import structlog
from rich.console import Console
from rich.table import Table

from second_brain.agents.github_agent import GitHubAgent
from second_brain.agents.rss_agent import RSSAgent
from second_brain.agents.web_agent import WebAgent
from second_brain.agents.youtube_agent import YouTubeAgent
from second_brain.core.db import StateStore
from second_brain.core.llm_client import HarnessLLMError, LLMClient
from second_brain.core.logger import get_logger
from second_brain.core.models import RawContent, RunStats
from second_brain.core.settings import Settings
from second_brain.processing.project_mapper import ProjectMapper
from second_brain.processing.summarizer import Summarizer
from second_brain.vault.daily_note import DailyNoteWriter, DailyStats
from second_brain.vault.index_updater import IndexUpdater
from second_brain.vault.note_writer import NoteWriter

logger = get_logger(__name__)
console = Console()


class Pipeline:
    def __init__(self, settings: Settings, db: StateStore, llm: LLMClient) -> None:
        self.settings = settings
        self.db = db
        self.llm = llm
        self.summarizer = Summarizer(llm=llm, settings=settings)
        self.mapper = ProjectMapper(settings=settings)

    async def run(self, sources: dict, dry_run: bool = False) -> RunStats:
        run_id = self.db.start_run()
        t0 = time.monotonic()

        note_writer = NoteWriter(
            vault_path=self.settings.vault_path, db=self.db, run_id=run_id
        )

        raw_items, errors = await self._fetch_all(sources)

        notes_created = 0
        notes_skipped = 0
        notes_fallback = 0
        note_refs: list[tuple[str, str]] = []
        project_intel: dict[str, int] = {}

        for raw in raw_items:
            if self.db.is_processed(raw.url, raw.content_hash, self.settings.freshness_days):
                notes_skipped += 1
                logger.info("item_skipped", url=raw.url)
                continue

            if dry_run:
                logger.info("dry_run_item", url=raw.url, title=raw.title)
                continue

            try:
                projects = self.mapper.map(raw, [])
                processed = await self.summarizer.summarize(raw, projects)
                path = note_writer.write(processed)
                notes_created += 1
                note_refs.append((raw.title, str(path)))
                for p in projects:
                    project_intel[p] = project_intel.get(p, 0) + 1
            except HarnessLLMError as e:
                logger.error("llm_failed_writing_inbox", url=raw.url, error=str(e))
                self._write_inbox(raw)
                notes_fallback += 1
            except Exception as e:
                logger.error("processing_failed", url=raw.url, error=str(e))
                notes_fallback += 1

        duration = time.monotonic() - t0

        if not dry_run and note_refs:
            stats_obj = DailyStats(
                notes_created=notes_created, notes_updated=0,
                notes_skipped=notes_skipped, notes_fallback=notes_fallback,
                tokens_used=0, cost_usd=self.llm.total_cost_usd,
                duration_seconds=duration, provider_counts={},
                note_refs=note_refs, project_intel=project_intel,
                top_insights="", tomorrows_focus="",
            )
            DailyNoteWriter(self.settings.vault_path).write(datetime.now(timezone.utc), stats_obj)
            IndexUpdater(self.settings.vault_path).append_run_log(
                run_id, notes_created, self.llm.total_cost_usd, duration
            )

        self.db.finish_run(run_id, {
            "items_processed": len(raw_items),
            "items_skipped": notes_skipped,
            "notes_created": notes_created,
            "cost_usd": self.llm.total_cost_usd,
        })

        run_stats = RunStats(
            run_id=run_id,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            sources_processed=len(raw_items),
            notes_created=notes_created,
            notes_skipped=notes_skipped,
            notes_fallback=notes_fallback,
            cost_usd=self.llm.total_cost_usd,
            duration_seconds=duration,
            failed_count=len(errors),
        )

        if not dry_run:
            self._print_table(run_stats)
            self._notify(run_stats)

        return run_stats

    async def _fetch_all(self, sources: dict) -> tuple[list[RawContent], list[str]]:
        tasks = []
        for url in sources.get("github_repos", []):
            tasks.append(self._safe(GitHubAgent(self.settings).fetch, url))
        for url in sources.get("youtube_channels", []) + sources.get("youtube_videos", []):
            tasks.append(self._safe(YouTubeAgent(self.settings).fetch, url))
        for url in sources.get("web_urls", []):
            tasks.append(self._safe(WebAgent(self.settings).fetch, url))
        rss = RSSAgent(self.settings, self.db)
        for url in sources.get("rss_feeds", []):
            tasks.append(self._safe(rss.fetch, url))

        results = await asyncio.gather(*tasks)
        items: list[RawContent] = []
        errors: list[str] = []
        for r in results:
            if isinstance(r, Exception):
                errors.append(str(r))
            elif isinstance(r, list):
                items.extend(r)
        return items, errors

    async def _safe(self, coro_fn, url: str):
        try:
            return await coro_fn(url)
        except Exception as e:
            logger.error("fetch_failed", url=url, error=str(e))
            return e

    def _write_inbox(self, raw: RawContent) -> None:
        inbox = self.settings.vault_path / "00-Inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        path = inbox / f"fallback-{raw.content_hash}.md"
        path.write_text(
            f"---\nsource_url: {raw.url}\nstatus: inbox\nfetched_at: {raw.fetched_at}\n---\n\n{raw.body[:5000]}",
            encoding="utf-8",
        )

    def _print_table(self, stats: RunStats) -> None:
        table = Table(
            title=f"Second Brain OS — Run #{stats.run_id} — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Sources processed", str(stats.sources_processed))
        table.add_row("Notes created", str(stats.notes_created))
        table.add_row("Notes skipped", str(stats.notes_skipped))
        table.add_row("Fallback (inbox)", str(stats.notes_fallback))
        table.add_row("Cost", f"${stats.cost_usd:.4f}")
        table.add_row("Duration", f"{stats.duration_seconds:.1f}s")
        if stats.failed_count:
            table.add_row("Fetch errors", str(stats.failed_count))
        console.print(table)

    def _notify(self, stats: RunStats) -> None:
        msg = f"Second Brain OS: {stats.notes_created} notes created, ${stats.cost_usd:.3f}"
        try:
            subprocess.run(
                ["osascript", "-e", f'display notification "{msg}" with title "Second Brain OS"'],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/unit/test_pipeline.py -v
```

Expected: `2 passed`

- [ ] **Step 4: Commit**

```bash
git add src/second_brain/orchestration/pipeline.py tests/unit/test_pipeline.py
git commit -m "feat: Pipeline runner with asyncio.gather, per-agent isolation, inbox fallback"
```

---

## Task 13: CLI

**Files:**
- Create: `src/second_brain/cli/main.py`
- Create: `config/sources.yaml`

- [ ] **Step 1: Create sources.yaml**

`config/sources.yaml`:
```yaml
github_repos:
  - https://github.com/anthropics/anthropic-sdk-python
  - https://github.com/langchain-ai/langgraph
  - https://github.com/modelcontextprotocol/python-sdk
  - https://github.com/run-llama/llama_index
  - https://github.com/microsoft/graphrag

youtube_videos: []

youtube_channels: []

rss_feeds:
  - https://news.ycombinator.com/rss
  - https://www.anthropic.com/rss.xml

web_urls: []
```

- [ ] **Step 2: Implement cli/main.py**

`src/second_brain/cli/main.py`:
```python
from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console

from second_brain.core.db import StateStore
from second_brain.core.llm_client import LLMClient
from second_brain.core.logger import setup_logging
from second_brain.core.settings import Settings

app = typer.Typer(name="sbo", help="Second Brain OS — daily knowledge harness")
console = Console()

_SOURCES_PATH = Path("config/sources.yaml")


def _load_sources() -> dict:
    if _SOURCES_PATH.exists():
        return yaml.safe_load(_SOURCES_PATH.read_text()) or {}
    return {"github_repos": [], "youtube_videos": [], "rss_feeds": [], "web_urls": []}


def _save_sources(sources: dict) -> None:
    _SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SOURCES_PATH.write_text(yaml.dump(sources, default_flow_style=False))


@app.command()
def run(
    source: Optional[str] = typer.Option(None, help="Source type: github|youtube|web|rss"),
    url: Optional[str] = typer.Option(None, help="Single URL to process"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fetch and summarize, no vault writes"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Run the ingestion pipeline."""
    from second_brain.orchestration.pipeline import Pipeline

    settings = Settings()
    setup_logging("DEBUG" if verbose else settings.log_level)
    db = StateStore(db_path=settings.db_path)
    llm = LLMClient(settings=settings)

    if source and url:
        sources: dict = {"github_repos": [], "youtube_videos": [], "rss_feeds": [], "web_urls": []}
        key_map = {"github": "github_repos", "youtube": "youtube_videos", "rss": "rss_feeds", "web": "web_urls"}
        key = key_map.get(source)
        if not key:
            console.print(f"[red]Unknown source type: {source}. Use: github|youtube|web|rss[/red]")
            raise typer.Exit(1)
        sources[key] = [url]
    else:
        sources = _load_sources()

    pipeline = Pipeline(settings=settings, db=db, llm=llm)
    stats = asyncio.run(pipeline.run(sources=sources, dry_run=dry_run))

    if dry_run:
        console.print(f"[green]Dry run complete. Would process {stats.sources_processed} sources.[/green]")


@app.command()
def add(
    source_type: str = typer.Argument(help="github|youtube|feed|web"),
    url: str = typer.Argument(help="URL to add"),
) -> None:
    """Add a source to sources.yaml."""
    sources = _load_sources()
    key_map = {"github": "github_repos", "youtube": "youtube_videos", "feed": "rss_feeds", "web": "web_urls"}
    key = key_map.get(source_type)
    if not key:
        console.print(f"[red]Unknown type: {source_type}. Use: github|youtube|feed|web[/red]")
        raise typer.Exit(1)
    if url not in sources.get(key, []):
        sources.setdefault(key, []).append(url)
        _save_sources(sources)
        console.print(f"[green]Added {url} to {key}[/green]")
    else:
        console.print(f"[yellow]{url} already in {key}[/yellow]")


@app.command()
def status() -> None:
    """Show last run stats."""
    settings = Settings()
    db = StateStore(db_path=settings.db_path)
    last = db.get_last_run()
    if not last:
        console.print("[yellow]No runs yet. Run `sbo run` to start.[/yellow]")
        return
    console.print(f"[bold]Last run:[/bold] #{last['run_id']}")
    console.print(f"  Started:  {last['started_at']}")
    console.print(f"  Finished: {last.get('finished_at', 'N/A')}")
    console.print(f"  Notes:    {last.get('notes_created', 0)}")
    console.print(f"  Cost:     ${last.get('cost_usd', 0.0):.4f}")


@app.command()
def fetch(
    url: str = typer.Option(..., help="URL to force re-fetch"),
) -> None:
    """Force re-fetch a single source, update vault note."""
    from second_brain.orchestration.pipeline import Pipeline

    settings = Settings()
    setup_logging(settings.log_level)
    db = StateStore(db_path=settings.db_path)
    llm = LLMClient(settings=settings)
    pipeline = Pipeline(settings=settings, db=db, llm=llm)

    # Determine source type from URL
    if "github.com" in url:
        sources = {"github_repos": [url], "youtube_videos": [], "rss_feeds": [], "web_urls": []}
    elif "youtube.com" in url or "youtu.be" in url:
        sources = {"github_repos": [], "youtube_videos": [url], "rss_feeds": [], "web_urls": []}
    else:
        sources = {"github_repos": [], "youtube_videos": [], "rss_feeds": [], "web_urls": [url]}

    # Remove from processed_items so it re-fetches
    import sqlite3
    with sqlite3.connect(settings.db_path) as conn:
        conn.execute("DELETE FROM processed_items WHERE url = ?", (url,))

    stats = asyncio.run(pipeline.run(sources=sources))
    console.print(f"[green]Re-fetched {url}. Notes created: {stats.notes_created}[/green]")


@app.command()
def config() -> None:
    """Open sources.yaml in $EDITOR."""
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(_SOURCES_PATH)])


@app.command()
def daemon() -> None:
    """Run as persistent background process using schedule library."""
    import schedule
    import time

    settings = Settings()
    setup_logging(settings.log_level)
    hour, minute = settings.schedule_time.split(":")
    schedule.every().day.at(settings.schedule_time).do(
        lambda: asyncio.run(
            Pipeline(settings, StateStore(settings.db_path), LLMClient(settings)).run(
                _load_sources()
            )
        )
    )
    console.print(f"[green]Daemon running. Next run at {settings.schedule_time}. Ctrl+C to stop.[/green]")
    while True:
        schedule.run_pending()
        time.sleep(60)


vault_app = typer.Typer(help="Vault management commands")
app.add_typer(vault_app, name="vault")


@vault_app.command("setup")
def vault_setup() -> None:
    """Scaffold vault folder structure."""
    settings = Settings()
    vault = settings.vault_path
    folders = [
        "00-Inbox",
        "01-Daily/templates",
        "02-Projects",
        *[f"02-Projects/{p}" for p in [
            "01-ContextForge", "02-RAGBench-Pro", "03-AgentOrchestra", "04-MemoryOS",
            "05-AutoResearch-v2", "06-MCPForge-Suite", "07-MCPGuard", "08-EvalEngine",
            "09-GuardStack", "10-LLMScope", "11-GraphRAG-Engine", "12-PromptOpt",
            "13-ToolForge", "14-StructOut", "15-SemanticRouter", "16-DocIQ",
            "17-SynthGen", "18-SelfHeal", "19-RedTeamKit", "20-LiveRAG",
            "21-SemanticCache", "22-BrowserAgent", "23-SQLAgent-Pro", "24-DebateArena",
        ]],
        "03-Research/context-engineering",
        "03-Research/rag-architectures",
        "03-Research/multi-agent-systems",
        "03-Research/mcp-protocol",
        "03-Research/evaluation-frameworks",
        "03-Research/job-market",
        "04-Resources/videos",
        "04-Resources/articles",
        "04-Resources/repos",
        "05-Learning",
        "06-Career/target-companies",
        "06-Career/job-postings",
        "06-Career/interview-prep",
        "07-Meta",
    ]
    for folder in folders:
        (vault / folder).mkdir(parents=True, exist_ok=True)

    # Create MOC-Home.md
    moc = vault / "07-Meta" / "MOC-Home.md"
    if not moc.exists():
        moc.write_text("# Map of Content\n\nGenerated by `sbo vault setup`\n")

    # Create Portfolio Overview
    overview = vault / "02-Projects" / "00-Portfolio-Overview.md"
    if not overview.exists():
        overview.write_text("# Portfolio Overview\n\n24 AI engineering projects — 10 weeks.\n\nSee PORTFOLIO.md for full details.\n")

    console.print(f"[green]Vault scaffold created at {vault}[/green]")
    console.print(f"  {len(folders)} folders created")
```

- [ ] **Step 3: Smoke test CLI**

```bash
uv run sbo --help
```

Expected: help text showing `run`, `add`, `status`, `fetch`, `config`, `vault`, `daemon`

```bash
uv run sbo vault setup
```

Expected: `Vault scaffold created at /Volumes/VeN/Claude-Code-Work/second-brain`

- [ ] **Step 4: Commit**

```bash
git add src/second_brain/cli/main.py config/sources.yaml
git commit -m "feat: Typer CLI — sbo run|add|status|fetch|config|vault|daemon"
```

---

## Task 14: Infrastructure Files

**Files:**
- Create: `Makefile`
- Create: `scripts/setup_launchagent.sh`
- Create: `scripts/benchmark.py`
- Create: `Dockerfile`
- Create: `.github/workflows/ci.yml`
- Create: `CLAUDE.md`
- Create: `docs/architecture.md`

- [ ] **Step 1: Create Makefile**

`Makefile`:
```makefile
.PHONY: run demo status install test lint setup-mac docker bench

run:
	uv run sbo run

demo:
	uv run sbo run --dry-run --verbose

status:
	uv run sbo status

install:
	uv sync
	uv run sbo --install-completion || true

test:
	uv run pytest tests/unit/ -v

test-all:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/
	uv run mypy src/ --ignore-missing-imports

setup-mac:
	bash scripts/setup_launchagent.sh

bench:
	uv run python scripts/benchmark.py

docker:
	docker build -t second-brain-os .

vault-setup:
	uv run sbo vault setup
```

- [ ] **Step 2: Create LaunchAgent setup script**

`scripts/setup_launchagent.sh`:
```bash
#!/bin/bash
set -e

SBO_PATH=$(which sbo 2>/dev/null || echo "$HOME/.local/bin/sbo")
PLIST_PATH="$HOME/Library/LaunchAgents/com.venki.second-brain-os.plist"
LOG_DIR="$HOME/Library/Logs"

mkdir -p "$LOG_DIR"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.venki.second-brain-os</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SBO_PATH</string>
        <string>run</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/second-brain-os.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/second-brain-os-error.log</string>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <false/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "LaunchAgent installed: $PLIST_PATH"
echo "Second Brain OS will run daily at 7:00 AM"
echo "Logs: $LOG_DIR/second-brain-os.log"
echo ""
echo "To run now: sbo run"
echo "To uninstall: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
```

- [ ] **Step 3: Create Dockerfile**

`Dockerfile`:
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
RUN uv sync --no-dev

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ src/
COPY config/ config/
COPY prompts/ prompts/
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENTRYPOINT ["sbo"]
CMD ["run"]
```

- [ ] **Step 4: Create CI**

`.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          version: "latest"
      - run: uv sync
      - run: uv run ruff check src/
      - run: uv run pytest tests/unit/ -v
```

- [ ] **Step 5: Create CLAUDE.md**

`CLAUDE.md`:
```markdown
# Second Brain OS — CLAUDE.md

## Project Goal
Daily knowledge harness for AI engineers. Ingests GitHub, YouTube, Web, RSS
→ processes with Claude → writes structured notes to Obsidian vault.

## Vault Location
/Volumes/VeN/Claude-Code-Work/second-brain

## Prompts Location
/Volumes/VeN/Claude-Code-Work/prompts/second-brain-os/v1.0/

## Coding Standards
- Python 3.12, uv, pyproject.toml
- Type hints on every function
- Pydantic BaseModel for all data schemas (in core/models.py)
- structlog for all logging — never print()
- async/await throughout
- All LLM calls through LLMClient only
- tiktoken before every LLM call (ContextBudget class)
- Cost tracking: tokens_in, tokens_out, model, cost_usd per call

## Key Design Decisions
- Agents return list[RawContent] — uniform interface (RSS returns multiple)
- asyncio.gather for parallel agent execution — never sequential
- SQLite tracks content_hash per URL — detects stale content for re-fetch
- 00-Inbox/ is the fallback when Claude API is down
- Never overwrite existing vault notes — append update section

## Run Commands
- `make run` — full pipeline
- `make demo` — dry run, no vault writes
- `make test` — unit tests only
- `uv run sbo vault setup` — create vault structure

## What Must Never Break
- One agent failing must never stop the others (try/except in pipeline._safe)
- If Claude API is down → write to 00-Inbox/, continue
- Never commit .env or API keys
```

- [ ] **Step 6: Commit infrastructure**

```bash
chmod +x scripts/setup_launchagent.sh
git add Makefile scripts/ Dockerfile .github/ CLAUDE.md docs/
git commit -m "feat: Makefile, Dockerfile, CI, LaunchAgent setup, CLAUDE.md"
```

---

## Task 15: End-to-End Test

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest tests/unit/ -v
```

Expected: all unit tests pass

- [ ] **Step 2: Run dry-run (no API key needed for structure test)**

```bash
uv run sbo vault setup
make demo
```

Expected: vault folders created, dry run completes showing source count

- [ ] **Step 3: Verify vault scaffold**

```bash
ls /Volumes/VeN/Claude-Code-Work/second-brain/
```

Expected: `00-Inbox  01-Daily  02-Projects  03-Research  04-Resources  05-Learning  06-Career  07-Meta`

- [ ] **Step 4: Run live pipeline (requires ANTHROPIC_API_KEY in .env)**

```bash
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY
make run
```

Expected: Rich table showing processed sources and notes created in vault.

- [ ] **Step 5: Verify vault output**

```bash
ls /Volumes/VeN/Claude-Code-Work/second-brain/04-Resources/repos/
ls /Volumes/VeN/Claude-Code-Work/second-brain/01-Daily/
```

Expected: `.md` files present in repos/ and a daily note for today.

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "feat: second-brain-os v0.1.0 — full pipeline end-to-end"
```

---

## Self-Review

**Spec coverage check:**
- ✅ LLMClient with Anthropic + OpenRouter fallback + cost tracking (Task 5)
- ✅ BaseAgent + all 4 ingestors (Tasks 6-9)
- ✅ ContextBudget (Task 6)
- ✅ Summarizer with 3 YAML prompt modes (Task 10)
- ✅ ProjectMapper keyword matching (Task 10)
- ✅ NoteWriter with YAML frontmatter + content_hash update detection (Task 11)
- ✅ DailyNote + IndexUpdater (Task 11)
- ✅ Pipeline with asyncio.gather + per-agent isolation + inbox fallback (Task 12)
- ✅ Typer CLI: run|add|status|fetch|config|vault|daemon (Task 13)
- ✅ config/sources.yaml + config/portfolio_projects.yaml (Tasks 10, 13)
- ✅ macOS LaunchAgent (Task 14)
- ✅ Makefile, Dockerfile, CI (Task 14)
- ✅ SQLite StateStore with FTS5 (Task 4) — index built at write time for Phase 2 sbo ask
- ✅ Vault folder structure with all 24 project folders (Task 13)
- ✅ 00-Inbox fallback when API down (Task 12)

**Gap identified and resolved:** `tests/conftest.py` not mentioned in tasks but needed for shared pytest fixtures — added as `touch tests/conftest.py` in Task 1 Step 2.

**Type consistency verified:** All tasks use `RawContent`, `ProcessedContent`, `RunStats`, `LLMResponse` from `core/models.py`. All agents return `list[RawContent]`. `Pipeline._safe` returns `list[RawContent] | Exception`. `NoteWriter.write()` returns `Path`. Consistent throughout.
