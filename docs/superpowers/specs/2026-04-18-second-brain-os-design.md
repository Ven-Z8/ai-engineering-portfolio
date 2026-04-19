# Second Brain OS — Design Specification

**Date:** 2026-04-18  
**Author:** Venki  
**Status:** Approved  
**Project location:** `/Volumes/VeN/Claude-Code-Work/projects/second-brain-os`  
**Vault location:** `/Volumes/VeN/Claude-Code-Work/second-brain`  
**Portfolio role:** Foundation Project #0 — runs during all 24 project builds  

---

## 1. What We Are Building

Second Brain OS is a **knowledge harness** — not a summarizer.

The distinction matters. A summarizer writes dead snapshots. A harness maintains live references: every note is a portal back to its source with a stable URL, a staleness clock, and a content hash. The system knows what it knows, knows when it is stale, and can go get fresh information on demand.

**Daily use:** Ingests GitHub repos, YouTube videos, web documentation, RSS feeds each morning at 7am. Processes everything through Claude. Writes structured, interlinked Obsidian notes to the vault. Generates a daily briefing note.

**On-demand use:** `sbo ask`, `sbo fetch --url`, `sbo run --source youtube --url ...` — trigger re-fetch of any source, surface related vault notes, synthesize with current content.

**Phase 2 (after 48h):** MCP server exposing vault as tools for Claude Desktop. Hermes Agent integration for Telegram/Slack interface. Agent-to-agent communication between ingestors.

This is simultaneously:
1. A real daily-use tool running on Venki's Mac
2. Portfolio Project #0 — demonstrates context engineering, multi-agent orchestration, production pipelines
3. An open source Mac application targeting AI engineers

**48-hour target:** Full pipeline running end-to-end. `make run` writes real notes to vault.

---

## 2. Architecture

### 2.1 Project layout

```
second-brain-os/
├── CLAUDE.md
├── README.md
├── pyproject.toml               # uv managed, Python 3.12
├── Makefile
├── Dockerfile
├── .env.example
├── .github/workflows/ci.yml
├── config/
│   ├── sources.yaml             # repos, feeds, channels to monitor
│   └── portfolio_projects.yaml  # all 24 projects for ProjectMapper
├── prompts/
│   ├── summarize_video.yaml
│   ├── summarize_repo.yaml
│   └── summarize_article.yaml
├── scripts/
│   ├── benchmark.py
│   └── setup_launchagent.sh
├── src/second_brain/
│   ├── agents/                  # ingestors
│   ├── processing/              # Claude-powered processors
│   ├── vault/                   # obsidian writers
│   ├── orchestration/           # pipeline runner + scheduler
│   ├── core/                    # llm client, settings, logger
│   └── cli/                     # typer sbo commands
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evals/
└── docs/
    ├── architecture.md
    └── adding-sources.md
```

### 2.2 System diagram

```
                         config/sources.yaml
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │         Pipeline Runner              │
              │      asyncio.gather (parallel)       │
              └──┬──────────┬──────────┬──────────┬─┘
                 │          │          │          │
           GitHub       YouTube      Web        RSS
           Agent        Agent       Agent      Agent
                 │          │          │          │
                 └──────────┴──────────┴──────────┘
                                │
                         RawContent + metadata
                                │
                         ┌──────▼──────┐
                         │  Summarizer │  ← Claude (3 prompt modes)
                         │  + Project  │  ← maps to 24 portfolio projects
                         │  Mapper     │
                         └──────┬──────┘
                                │
                    ProcessedContent (summary, insights,
                    tags, project_relevance, cost_usd)
                                │
                         ┌──────▼──────┐
                         │  NoteWriter │  ← writes to correct vault folder
                         │  + Harness  │  ← content_hash, staleness clock
                         │  Layer      │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │  DailyNote  │  ← 01-Daily/YYYY-MM-DD.md
                         └──────┬──────┘
                                │
                    Rich terminal table + macOS notification

                  On re-fetch / query (sbo ask / sbo fetch):
                                │
                         ┌──────▼──────────────────┐
                         │  QueryResolver           │
                         │  1. FTS5 search vault    │
                         │  2. Check staleness      │
                         │  3. Re-fetch if stale    │
                         │  4. Diff content_hash    │
                         │  5. Synthesize answer    │
                         └──────────────────────────┘
```

### 2.3 LLM routing chain

```
Request
  │
  ▼
Anthropic SDK (claude-sonnet-4-6)   ← primary, always tried first
  │ on RateLimitError / APIError
  ▼
OpenRouter (configurable model)     ← fallback, same Anthropic-style API
  │ on failure
  ▼
Write raw content to 00-Inbox/      ← never crash the pipeline
Log warning + continue to next item
```

Model selection per task (Phase 2, after initial build):
- Summarization: `claude-sonnet-4-6` (balanced cost + quality)
- ProjectMapper (classification only): `claude-haiku-4-5` via OpenRouter (10x cheaper)
- Connection finding: `claude-haiku-4-5` via OpenRouter
- Daily note synthesis: `claude-sonnet-4-6` (high quality, runs once daily)

---

## 3. Components

### 3.1 Core — `src/second_brain/core/`

**`settings.py`** — `pydantic-settings BaseSettings`:
```python
class Settings(BaseSettings):
    anthropic_api_key: str
    openrouter_api_key: str = ""
    vault_path: Path = Path("/Volumes/VeN/Claude-Code-Work/second-brain")
    db_path: Path = Path("state/sbo.db")
    schedule_time: str = "07:00"
    default_model: str = "claude-sonnet-4-6"
    fallback_model: str = "anthropic/claude-sonnet-4-6"   # OpenRouter model id
    max_tokens_per_call: int = 8000
    freshness_days: int = 7                                # re-fetch threshold
```

**`logger.py`** — structlog with JSON output, level from env. Every log includes `run_id`, `source_type`, `url` in context vars.

**`llm_client.py`** — single abstraction used everywhere:
```python
@dataclass
class LLMClient:
    settings: Settings
    _total_cost_usd: float = 0.0      # tracks session total

    async def complete(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,     # override per-call
        max_tokens: int = 2048,
    ) -> LLMResponse:
        # 1. tiktoken count BEFORE call — log + enforce budget
        # 2. Try Anthropic SDK
        # 3. On failure, try OpenRouter via httpx
        # 4. On both failures, raise HarnessLLMError (caught by pipeline)
        # 5. Log: tokens_in, tokens_out, model, cost_usd, latency_ms
```

```python
@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    provider: str   # "anthropic" | "openrouter"
```

**`db.py`** — SQLite with these tables:
- `processed_items(url, source_type, content_hash, fetched_at, note_path, run_id)`
- `run_log(run_id, started_at, finished_at, items_processed, items_skipped, notes_created, tokens_used, cost_usd)`
- `run_events(run_id, ts, level, message, url)` — per-item events
- `notes_content(url, title, summary, tags, note_path)` — denormalized table for FTS5
- `fts_notes` — SQLite FTS5 virtual table over `notes_content` for `sbo ask` (Phase 2)

### 3.2 Agents — `src/second_brain/agents/`

All agents inherit `BaseAgent`:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> RawContent:
        ...
    
    def should_refetch(self, url: str, db: StateStore) -> bool:
        """Return True if url is new or stale beyond freshness_threshold."""
        ...
```

`RawContent` is a Pydantic `BaseModel` (defined in `core/models.py`, imported everywhere — single source of truth):

**`github_agent.py`** — ported from `obsidian-daily-agent`:
- Fetches README.md + recent commits (last 7 days) via GitHub API
- Fetches open issues labeled `good first issue` or `enhancement`
- Uses `httpx` async, unauthenticated for public repos
- `metadata`: `repo_name`, `stars`, `last_commit_sha`, `open_issues_count`

**`youtube_agent.py`** — ported from `obsidian-daily-agent`:
- Extracts transcript via `youtube-transcript-api`
- Extracts metadata via YouTube oEmbed API (title, channel, duration)
- Falls back to next available language if English unavailable
- **Research handoff**: returns `description_urls: list[str]` for WebAgent
- `metadata`: `video_id`, `channel`, `duration_seconds`, `published_at`

**`web_agent.py`** — ported from `obsidian-daily-agent`:
- `httpx` + `BeautifulSoup` — strips nav/footer/ads
- Detects paywall (content < 500 chars after strip → log + skip)
- Accepts URLs from YouTubeAgent description handoff
- `metadata`: `publication_date`, `author`, `domain`

**`rss_agent.py`** — new:
- `feedparser` for parsing
- Last N items (default 10, configurable per feed in `sources.yaml`)
- Deduplicates against `processed_items` table
- `metadata`: `feed_title`, `item_published_at`, `categories`

### 3.3 Processing — `src/second_brain/processing/`

**`summarizer.py`** — loads prompts from `prompts/*.yaml`, calls `LLMClient`:

Three modes, each prompt produces this Obsidian-ready structure:
```markdown
## Summary
3-5 bullet points

## Key Insights
What is new or important — not obvious from title alone

## Relevance to My Work
Maps content to specific portfolio projects using ProjectMapper output

## Tags
auto-generated kebab-case tags

## Links
URLs referenced in the content
```

**`project_mapper.py`** — reads `config/portfolio_projects.yaml` (all 24 projects with `name`, `description`, `key_technologies`). Phase 1: keyword intersection between note content and project tech lists. Phase 2: embedding cosine similarity. Returns `list[str]` of project folder names (e.g., `["03-AgentOrchestra", "05-AutoResearch"]`).

**`context_budget.py`** — enforces 8000 token limit per summarization call:
```python
class ContextBudget:
    max_tokens: int = 8000
    
    def fit(self, text: str, model: str) -> str:
        """Truncate text to fit within budget, preserving structure."""
```
This class gets named in the README — it's a portfolio signal for context engineering.

### 3.4 Vault — `src/second_brain/vault/`

**`note_writer.py`** — writes processed notes to vault:

Routing logic:
```
SourceType.YOUTUBE    → 04-Resources/videos/
SourceType.GITHUB_REPO → 04-Resources/repos/
SourceType.WEB_DOC    → 04-Resources/articles/
SourceType.RSS        → 04-Resources/articles/
```

Note filename: `{slugify(title)}-{source_id[:8]}.md`

YAML frontmatter on every note:
```yaml
---
title: "LangGraph: Multi-Agent Orchestration Deep Dive"
source_url: https://www.youtube.com/watch?v=...
source_type: youtube
source_id: abc123de
content_hash: 4f8e2a1b         # staleness detection
fetched_at: 2026-04-18T07:12Z
updated_at: 2026-04-18T07:12Z
tags: [langgraph, multi-agent, langchain, graph-state]
projects: [03-AgentOrchestra, 05-AutoResearch, 18-SelfHeal]
cost_usd: 0.0031
tokens_used: 1840
provider: anthropic
status: curated
---
```

Write rules:
- New URL → create note
- Same URL, same `content_hash` → skip (deduplicated)
- Same URL, different `content_hash` → append `## Update — YYYY-MM-DD` section
- API down → write raw content to `00-Inbox/` with frontmatter, log warning

**`daily_note.py`** — creates/updates `01-Daily/YYYY-MM-DD.md`:
```markdown
# 2026-04-18

## Pipeline Summary
- Processed: 15 sources in 2m 14s
- Notes created: 12 | Updated: 2 | Skipped: 1 (dupe)
- Tokens used: 18,400 | Cost: $0.061
- Provider: anthropic (12) | openrouter (1) | inbox-fallback (2)

## New Notes
- [[langgraph-multi-agent-orchestration-abc123de]] — LangGraph deep dive
- [[graphrag-microsoft-repo-de4f8a2b]] — Microsoft GraphRAG repo update

## Project Intel
- **03-AgentOrchestra**: 3 new sources
- **11-GraphRAG-Engine**: 2 new sources

## Top Insights
1. LangGraph's new `interrupt()` primitive simplifies HITL checkpoints significantly
2. Microsoft GraphRAG added community-level summarization — relevant to Project 11
3. Hacker News: MCP adoption accelerating — 3 posts in 24h

## Tomorrow's Focus
Based on today's pipeline: review LangGraph interrupt() for AgentOrchestra build
```

**`index_updater.py`** — maintains `07-Meta/MOC-Home.md` and `07-Meta/pipeline-log.md`. Appends one-line entry per run to `pipeline-log.md`.

### 3.5 Orchestration — `src/second_brain/orchestration/`

**`pipeline.py`** — main orchestrator:

```python
async def run(settings: Settings, db: StateStore, sources: SourceConfig) -> RunStats:
    # 1. Start run_id in db
    # 2. asyncio.gather all agent fetches — each wrapped in try/except
    # 3. For each RawContent: check should_refetch() → skip or process
    # 4. Summarize → ProjectMap → Write note (sequential per item, parallel across items)
    # 5. Update daily note
    # 6. Update MOC + pipeline-log
    # 7. Print Rich table
    # 8. macOS notification via osascript
    # 9. Finalize run_id in db with stats
```

Per-agent isolation: if `GitHubAgent` raises, the YouTube/Web/RSS agents continue unaffected. Error is logged and counted in `RunStats.failed_count`.

**`scheduler.py`** — wraps `schedule` library. Used by `sbo daemon` command (runs as persistent background process, not LaunchAgent — LaunchAgent just calls `sbo run` once at 7am and exits).

### 3.6 CLI — `src/second_brain/cli/`

**`main.py`** — Typer app, entry point for `sbo` command:

```
sbo run                                   # full pipeline
sbo run --source github --url <url>       # single source
sbo run --dry-run                         # fetch + summarize, no vault writes
sbo add github <url>                      # append to sources.yaml
sbo add youtube <url>
sbo add feed <url>
sbo add web <url>
sbo fetch --url <url>                     # force re-fetch, update vault note
sbo fetch --url <url>                     # force re-fetch, update vault note
sbo status                                # last run stats + next scheduled time
sbo daemon                                # run as persistent background process (alternative to LaunchAgent)
sbo vault setup                           # scaffold vault folder structure
sbo config                                # open sources.yaml in $EDITOR
```

---

## 4. Data Models

All Pydantic `BaseModel`:

```python
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
    content_hash: str         # sha256(body)[:16]
    metadata: dict[str, str]
    fetched_at: datetime

class ProcessedContent(BaseModel):
    raw: RawContent
    summary: str
    key_insights: list[str]
    tags: list[str]
    project_relevance: list[str]   # portfolio project folder names
    relevance_note: str            # one sentence: why this matters to my work
    cost_usd: float
    tokens_in: int
    tokens_out: int
    provider: str

class RunStats(BaseModel):
    run_id: int
    started_at: datetime
    finished_at: datetime
    sources_processed: int
    notes_created: int
    notes_updated: int
    notes_skipped: int
    notes_fallback: int            # written to 00-Inbox
    tokens_used: int
    cost_usd: float
    duration_seconds: float
    provider_counts: dict[str, int]  # {"anthropic": 12, "openrouter": 1}
```

---

## 5. Vault Structure

Full folder structure created by `sbo vault setup`:

```
second-brain/
├── 00-Inbox/                    ← fallback when API down
├── 01-Daily/                    ← YYYY-MM-DD.md daily briefings
│   └── templates/
│       └── daily-template.md
├── 02-Projects/                 ← one folder per portfolio project
│   ├── 00-Portfolio-Overview.md
│   ├── 01-ContextForge/
│   ├── 02-RAGBench-Pro/
│   ├── 03-AgentOrchestra/
│   ├── 04-MemoryOS/
│   ├── 05-AutoResearch-v2/
│   ├── 06-MCPForge-Suite/
│   ├── 07-MCPGuard/
│   ├── 08-EvalEngine/
│   ├── 09-GuardStack/
│   ├── 10-LLMScope/
│   ├── 11-GraphRAG-Engine/
│   ├── 12-PromptOpt/
│   ├── 13-ToolForge/
│   ├── 14-StructOut/
│   ├── 15-SemanticRouter/
│   ├── 16-DocIQ/
│   ├── 17-SynthGen/
│   ├── 18-SelfHeal/
│   ├── 19-RedTeamKit/
│   ├── 20-LiveRAG/
│   ├── 21-SemanticCache/
│   ├── 22-BrowserAgent/
│   ├── 23-SQLAgent-Pro/
│   └── 24-DebateArena/
├── 03-Research/
│   ├── context-engineering/
│   ├── rag-architectures/
│   ├── multi-agent-systems/
│   ├── mcp-protocol/
│   ├── evaluation-frameworks/
│   └── job-market/
├── 04-Resources/                ← pipeline writes here
│   ├── videos/                  ← YouTube notes
│   ├── articles/                ← Web + RSS notes
│   └── repos/                   ← GitHub notes
├── 05-Learning/
├── 06-Career/
│   ├── target-companies/
│   ├── job-postings/
│   └── interview-prep/
└── 07-Meta/
    ├── MOC-Home.md              ← master map of content
    ├── MOC-Projects.md
    └── pipeline-log.md          ← one line per run, appended
```

---

## 6. Harness Layer — Re-fetch and Query

This is the design element that makes Second Brain OS a harness, not an archiver.

### 6.1 Staleness detection

Every `processed_items` row stores `content_hash`. On re-fetch:
- Same hash → skip, log "unchanged"
- Different hash → update note with `## Update — YYYY-MM-DD` appended section
- `freshness_threshold` is configurable per source type in `sources.yaml`

### 6.2 Force re-fetch

```bash
sbo fetch --url https://github.com/langchain-ai/langgraph
```

1. Fetches current content
2. Computes new `content_hash`
3. Compares to stored hash
4. If changed: re-summarizes diff, appends update section to vault note
5. Updates `processed_items` with new hash and `fetched_at`

### 6.3 SQLite FTS5 index

`sbo ask "what did I learn about LangGraph interrupts?"` (Phase 2, index built in Phase 1):

```sql
-- notes_content is populated by NoteWriter on every note create/update
CREATE TABLE notes_content(url, title, summary, tags, note_path);
CREATE VIRTUAL TABLE fts_notes USING fts5(
    url, title, summary, tags,
    content='notes_content',
    tokenize='porter unicode61'
);
```

Phase 1: build and maintain the index. Phase 2: wire `sbo ask` to search FTS5 + call Claude with matching notes as context.

### 6.4 Agent handoff (Phase 2)

YouTubeAgent returns `description_urls: list[str]` alongside `RawContent`. Pipeline runner feeds these to WebAgent automatically. This is the first agent-to-agent communication pattern — WebAgent enriches YouTube notes with content from linked resources.

### 6.5 MCP server (Phase 2)

Exposes vault as tools for Claude Desktop / Hermes Agent:
- `search_vault(query: str) -> list[NoteRef]`
- `get_note(url: str) -> NoteContent`
- `refresh_source(url: str) -> RefreshResult`

Hermes Agent integration: Telegram/Slack gateway → Hermes → MCP → vault.

---

## 7. Error Handling

**Rule: one agent failing must never stop the others.**

```
Pipeline run with 15 sources:
  GitHubAgent(repo_1)     → ✓ success
  GitHubAgent(repo_2)     → ✗ timeout → logged, counted in failed_count
  YouTubeAgent(video_1)   → ✓ success
  RSSAgent(hn_feed)       → ✗ feedparser error → logged, continues
  WebAgent(url_1)         → ✓ success

Result: 12 processed, 3 failed — pipeline completes, Rich table shows failures
```

**Claude API down:**
- `LLMClient` tries Anthropic → fails → tries OpenRouter → fails
- `HarnessLLMError` raised
- `NoteWriter` catches it → writes raw `RawContent` to `00-Inbox/` with frontmatter
- Daily note includes `## Inbox (needs processing)` section listing fallback items
- Next run: `sbo run` processes inbox items first

**Vault write failure:**
- If vault path not accessible (external drive unmounted) → abort run immediately, log critical
- `sbo status` shows last run result including abort reason

---

## 8. Open Source Packaging

### 8.1 README formula (portfolio-grade)

1. One-line hook: *"GitHub repos, YouTube transcripts, docs, feeds — summarized daily, wired into Obsidian, and queryable on demand."*
2. Benchmark table: sources processed, avg cost per run, notes/day, re-fetch latency
3. Install: 3 lines (`uv tool install second-brain-os` + set key + `sbo vault setup`)
4. Architecture ASCII diagram
5. Real code example: the `LLMClient` with cost tracking
6. Eval: 30-day vault stats, note quality score

### 8.2 macOS LaunchAgent

`scripts/setup_launchagent.sh` creates `~/Library/LaunchAgents/com.venki.second-brain-os.plist`:
- Runs `sbo run` at 07:00 daily
- Logs stdout + stderr to `~/Library/Logs/second-brain-os.log`
- `RunAtLoad: false` (don't run on install, wait for next 7am)
- `KeepAlive: false` (it's a one-shot run, not a daemon)

### 8.3 CI

`.github/workflows/ci.yml`: ruff + mypy on push, pytest unit tests, no integration tests in CI (they need API keys).

---

## 9. Phase 1 (48h) Scope

Build in this exact order. Test each component before moving to the next.

| Step | Component | Test command |
|------|-----------|-------------|
| 1 | Vault scaffold (`sbo vault setup`) | `ls second-brain/` — all 8 folders present |
| 2 | `pyproject.toml` + `uv sync` | `uv run python -c "import second_brain; print('ok')"` |
| 3 | `core/settings.py` + `core/logger.py` | `uv run python -c "from second_brain.core.settings import Settings; print(Settings())"` |
| 4 | `core/llm_client.py` | `uv run python -c "import asyncio; from second_brain.core.llm_client import LLMClient; ..."` |
| 5 | `agents/github_agent.py` | `uv run python -m second_brain.agents.github_agent https://github.com/langchain-ai/langgraph` |
| 6 | `agents/youtube_agent.py` | Single video fetch test |
| 7 | `agents/web_agent.py` | Single URL fetch test |
| 8 | `agents/rss_agent.py` | `https://news.ycombinator.com/rss` test |
| 9 | `processing/summarizer.py` | Summarize one RawContent, print result |
| 10 | `processing/project_mapper.py` | Map one note, print matched projects |
| 11 | `vault/note_writer.py` | Write one note, inspect file |
| 12 | `vault/daily_note.py` | Generate daily note, inspect file |
| 13 | `orchestration/pipeline.py` | `make demo` — dry run, no vault writes |
| 14 | `cli/main.py` | `make run` — full pipeline, real vault writes |
| 15 | `scripts/setup_launchagent.sh` | `make setup-mac` |
| 16 | README + Makefile + Dockerfile + CI | Push to GitHub |

### 9.1 Phase 1 success criteria

```bash
make run

# Expected Rich table output:
# ┌─────────────────────────────────────────────────────────┐
# │ Second Brain OS — Run #1 — 2026-04-18 07:00             │
# ├────────────────┬────────┬──────────┬────────────────────┤
# │ Source         │ Status │ Notes    │ Cost               │
# ├────────────────┼────────┼──────────┼────────────────────┤
# │ GitHub (5)     │ ✓      │ 5 new    │ $0.021             │
# │ YouTube (2)    │ ✓      │ 2 new    │ $0.018             │
# │ RSS - HN (10)  │ ✓      │ 8 new    │ $0.014             │
# │ RSS - Anth (5) │ ✓      │ 4 new    │ $0.009             │
# ├────────────────┼────────┼──────────┼────────────────────┤
# │ Total          │        │ 19 notes │ $0.062 | 2m 14s    │
# └────────────────┴────────┴──────────┴────────────────────┘

ls second-brain/04-Resources/repos/      # 5 github notes
ls second-brain/04-Resources/videos/     # 2 youtube notes
ls second-brain/04-Resources/articles/   # 12 rss/web notes
ls second-brain/01-Daily/               # 2026-04-18.md
```

---

## 10. Phase 2 Roadmap

Not in scope for 48h. Planned for later sessions:

- [ ] Port Wiki compiler + extractor from `obsidian-daily-agent` (interlinked concept pages)
- [ ] `sbo ask "<question>"` — FTS5 + Claude synthesis
- [ ] `sbo fetch --url` with diff detection
- [ ] Model routing per task type (Haiku for classification, Sonnet for synthesis)
- [ ] MCP server exposing vault tools
- [ ] Hermes Agent integration (Telegram/Slack query interface)
- [ ] Agent-to-agent: YouTube description URLs handed to WebAgent
- [ ] rumps macOS menu bar app with status indicator
- [ ] Semantic search via Qdrant embeddings
- [ ] `sbo bench` — measure note quality, cost per note, staleness stats

---

## 11. Dependencies (`pyproject.toml`)

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
    "PyGithub>=2.0.0",
    "aiofiles>=23.0.0",
    "PyYAML>=6.0.0",
    "schedule>=1.2.0",
    "python-frontmatter>=1.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "ruff>=0.4.0", "mypy>=1.9.0"]

[project.scripts]
sbo = "second_brain.cli.main:app"
```

---

## 12. Portfolio Narrative

When a hiring manager reads the Second Brain OS GitHub repo, they should see:

- **Context Engineering**: `ContextBudget` class enforces token limits before every Claude call
- **Multi-Agent Orchestration**: 4 independent agents run in parallel via `asyncio.gather`, isolated failure handling
- **Production Error Handling**: graceful degradation to `00-Inbox/`, never crashes, detailed run stats
- **Harness thinking**: every note stores `content_hash` + `canonical_url` — the system knows when its knowledge is stale
- **Cost consciousness**: every LLM call tracked, aggregated per run, shown in Rich table — $0.06/day
- **Real daily use**: this isn't a demo. It's been running for [N] days and produced [N] notes.

The vault itself is a live artifact. After 10 weeks of building the 24 projects, the vault contains 500+ structured notes on exactly the topics those projects cover. That is the portfolio.
