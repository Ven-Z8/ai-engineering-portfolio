# Second Brain OS — Portfolio Project #0

- Task: `second-brain-os-project-0`
- Current Owner: `codex`
- Status: `active`
- Last Updated: `2026-04-19 - codex`
- Next Action: `Continue from committed SBO project at projects/second-brain-os. Next slice: build LangGraph sbo research loop on top of existing EmbeddingGemma + ChromaDB vault index and sbo ask foundation.`

## Current Owner
codex

## Status
active

## Next Action
Build the research agent architecture on top of the committed SBO baseline: LangGraph research loop + existing ChromaDB/EmbeddingGemma vault index + report writing into Brain/02-Projects/<project>/research.md. MCP stdio server comes after the CLI research loop works.

---

## Objective

Build Portfolio Project #0, Second Brain OS, as the daily knowledge harness that runs across all 24 portfolio projects and ports proven capabilities from obsidian-daily-agent into a new standalone project.

## Current State

Approved spec and implementation plan exist under docs/superpowers. The target project directory projects/second-brain-os does not exist yet. The closest source implementation is projects/obsidian-daily-agent, which already contains ingestion, provider routing, wiki, and vault-writing foundations.

Decision recorded on 2026-04-19: keep `second-brain-os` as the clean standalone portfolio project. Treat `projects/obsidian-daily-agent` as the source repo to port from selectively, not the final portfolio artifact.

## Working Agreements

- Keep important decisions here.
- Leave a handoff entry before stopping.
- Prefer exact next steps over vague summaries.

## Important Files

- Add files that matter for this task.

## Risks / Blockers

- None yet.

## Session Handoffs

### 2026-04-19 00:14 UTC - codex

- Summary: Oriented the workspace for the portfolio workstream, confirmed that Second Brain OS is the approved Foundation Project #0, identified docs/superpowers/specs/2026-04-18-second-brain-os-design.md and docs/superpowers/plans/2026-04-18-second-brain-os.md as today’s source-of-truth plan/spec, and verified that the target project directory has not been created yet. Confirmed projects/obsidian-daily-agent is the source repo intended to be ported from.
- Files: docs/agent-handoff/tasks/second-brain-os-project-0.md, docs/agent-handoff/ACTIVE_TASKS.md, docs/superpowers/specs/2026-04-18-second-brain-os-design.md, docs/superpowers/plans/2026-04-18-second-brain-os.md, projects/obsidian-daily-agent/README.md
- Commands: sed -n '1,260p' docs/superpowers/specs/2026-04-18-second-brain-os-design.md, sed -n '1,260p' docs/superpowers/plans/2026-04-18-second-brain-os.md, sed -n '1,260p' projects/obsidian-daily-agent/README.md, python3 scripts/agent_handoff.py new-task ...
- Blockers: projects/second-brain-os does not exist yet, Workspace is dirty, so new implementation should avoid disturbing unrelated ongoing changes
- Next: Start implementation at Task 1 in docs/superpowers/plans/2026-04-18-second-brain-os.md by scaffolding projects/second-brain-os, unless the project scope or first slice should be narrowed before coding.

### 2026-04-19 00:21 UTC - codex

- Summary: Chose the implementation strategy for Project #0: build the smallest real vertical slice first instead of completing all broad foundation tasks before any visible output. The first slice should prove the project by scaffolding second-brain-os and getting one source ingested into one real Obsidian note.
- Files: docs/agent-handoff/tasks/second-brain-os-project-0.md, docs/agent-handoff/ACTIVE_TASKS.md
- Commands: python3 scripts/agent_handoff.py handoff ...
- Blockers: Need to keep scope tight so Project #0 ships as a clean portfolio artifact instead of inheriting too much donor complexity.
- Next: Implement the minimum vertical slice in projects/second-brain-os: scaffold the project, add core settings/models, port one simple ingestor from obsidian-daily-agent, and write one real note to the vault before expanding the rest of the plan.

### 2026-04-19 00:30 UTC - codex

- Summary: Created an isolated worktree for Project #0 and scaffolded projects/second-brain-os with the first working vertical slice. Implemented core models, a minimal GitHub repo agent, and a vault note writer. Verified the first source-to-note loop locally and got the first unit test batch passing.
- Files: .gitignore, .worktrees/second-brain-os-project-0/projects/second-brain-os/pyproject.toml, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/models.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/agents/github_agent.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/vault/note_writer.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_models.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_github_agent.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_note_writer.py
- Commands: git worktree add .worktrees/second-brain-os-project-0 -b chore/second-brain-os-project-0, uv sync, uv sync --extra dev, uv run pytest tests/unit/test_models.py tests/unit/test_github_agent.py tests/unit/test_note_writer.py -q
- Blockers: obsidian-daily-agent is still the donor repo; porting should stay selective so second-brain-os remains a clean portfolio artifact, Live remote ingestion still needs later verification against real network/API access
- Next: Expand the first slice into a more real Project #0 foundation: add settings and vault scaffold support, then choose the next source or pipeline layer before broadening to the full Second Brain OS plan.

### 2026-04-19 00:41 UTC - codex

- Summary: Extended the verified Project #0 slice beyond the initial GitHub-to-note path. Added pydantic settings, structlog logger, vault scaffold logic for the full 24-project folder layout, and a minimal Typer CLI with sbo vault setup. Verified the scaffold command against a temporary vault path and ran the full current unit suite successfully.
- Files: .worktrees/second-brain-os-project-0/projects/second-brain-os/pyproject.toml, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/settings.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/logger.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/vault/scaffold.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/cli/main.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_settings.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_vault_scaffold.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_cli.py
- Commands: .venv/bin/python -m pytest tests/unit/test_settings.py tests/unit/test_vault_scaffold.py tests/unit/test_cli.py -q, .venv/bin/sbo --help, VAULT_PATH=<tmp> .venv/bin/sbo vault setup, .venv/bin/python -m pytest tests/unit -q
- Blockers: The worktree branch contains the active implementation; nothing has been committed yet., Real remote ingestion and end-to-end pipeline orchestration are still the next major slice.
- Next: Build the next vertical layer on top of the clean scaffold: either wire a real pipeline entrypoint around the GitHub source path, or add the next ingestor and shared processing contract before broadening to daily-note generation.

### 2026-04-19 00:45 UTC - codex

- Summary: Added the next runnable layer for Project #0. Aligned NoteWriter with the approved second-brain vault structure, added a simple processing layer, created a minimal synchronous pipeline for GitHub sources, added config/sources.yaml, and extended the CLI with sbo run. Verified the run command surface and the full current unit suite.
- Files: .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/models.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/vault/note_writer.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/processing/simple_processor.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/orchestration/pipeline.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/cli/main.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/config/sources.yaml, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_note_writer.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_pipeline.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_cli.py
- Commands: .venv/bin/python -m pytest tests/unit/test_note_writer.py tests/unit/test_pipeline.py tests/unit/test_cli.py -q, .venv/bin/sbo run --help, .venv/bin/python -m pytest tests/unit -q
- Blockers: The current pipeline is intentionally minimal and synchronous; persistence, dedupe, and LLM-based summarization are still future layers., Running against real remote GitHub URLs still depends on network access and should be verified in a later step.
- Next: Choose the next meaningful layer: add a persistent state store and duplicate detection, or add the next source type (web or RSS) while keeping the pipeline simple and clean.

### 2026-04-19 00:47 UTC - codex

- Summary: Created the first real Obsidian artifact with second-brain-os against the actual vault path. Ran sbo vault setup on /Volumes/VeN/Claude-Code-Work/second-brain and wrote a repo note for the local obsidian-daily-agent donor project into 04-Resources/repos.
- Files: second-brain/04-Resources/repos/2026-04-19-local-obsidian-daily-agent.md, docs/agent-handoff/tasks/second-brain-os-project-0.md
- Commands: .venv/bin/sbo vault setup, write first repo artifact into second-brain/04-Resources/repos
- Blockers: Current local-repo artifact uses a file:// source URL and includes generated .venv files in the structure preview; good enough for the first success, but not yet portfolio-polished.
- Next: Tighten artifact quality before scaling up: filter generated/noisy paths like .venv and cache folders out of the GitHub repo structure preview, then create the next artifact from a cleaner source input or through the sbo run path.

### 2026-04-19 00:52 UTC - codex

- Summary: Repointed second-brain-os to the actual Obsidian vault at /Volumes/VeN/Claude-Code-Work/second-brain/Portfolio, scaffolded that vault, and wrote the first repo artifact into the live Obsidian folder structure so it is visible in the user's active vault.
- Files: .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/settings.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_settings.py, second-brain/Portfolio/04-Resources/repos/2026-04-19-local-obsidian-daily-agent.md
- Commands: .venv/bin/sbo vault setup, write repo artifact into second-brain/Portfolio/04-Resources/repos
- Blockers: Current first artifact is visible in the correct vault but still includes generated repo noise like .venv content in the structure preview.
- Next: Improve artifact quality inside the real Portfolio vault by filtering noisy generated repo files out of the structure preview, then create the next artifact through the normal sbo run path.

### 2026-04-19 00:57 UTC - codex

- Summary: Cleaned repo artifact quality for the GitHub ingestion path. Added filtering in GitHubRepoAgent so structure previews now skip generated and noisy paths such as .venv, .git, __pycache__, .pytest_cache, build, dist, and similar cache/output directories. Re-ran the full unit suite and regenerated the first Portfolio-vault artifact with the cleaner structure preview.
- Files: .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/agents/github_agent.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_github_agent.py, second-brain/Portfolio/04-Resources/repos/2026-04-19-local-obsidian-daily-agent.md
- Commands: .venv/bin/python -m pytest tests/unit/test_github_agent.py -q, .venv/bin/python -m pytest tests/unit -q, regenerate Portfolio repo artifact with cleaned structure preview
- Blockers: Artifact quality is improved, but the pipeline is still intentionally minimal; persistent state, dedupe, and richer summarization remain the next major work.
- Next: Return to the broader Claude plan from a cleaner baseline. The next major layer should follow the approved plan sequence and add the first production-shaped persistence/orchestration pieces instead of polishing this artifact further.

### 2026-04-19 01:02 UTC - codex

- Summary: Implemented the next major production-shaped layer from the approved plan: SQLite-backed persistent state and duplicate detection. Added core/db.py with processed item tracking, wired dedupe into the current pipeline so unchanged sources are skipped, and expanded tests to cover both database behavior and pipeline duplicate skipping. Adjusted pipeline/CLI tests to use isolated temp DB paths so the suite remains repeatable.
- Files: .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/db.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/models.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/orchestration/pipeline.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_db.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_pipeline.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/tests/unit/test_cli.py
- Commands: .venv/bin/python -m pytest tests/unit/test_db.py tests/unit/test_pipeline.py -q, .venv/bin/python -m pytest tests/unit -q
- Blockers: StateStore currently covers processed item tracking only; broader run logs and note indexing from the full Claude plan are still future work.
- Next: Continue following the approved plan from this stronger baseline: the next best layer is richer summarization or the next source type, but now the system has memory and rerun safety.

### 2026-04-19 01:08 UTC - codex

- Summary: Prepared a clean handoff for Claude on Second Brain OS Project #0. The isolated implementation lives in the worktree branch with a working Portfolio vault target, first real Obsidian artifact written, cleaned GitHub repo structure previews, a runnable sbo CLI, a minimal GitHub pipeline, and SQLite-backed dedupe/persistent state. The current system is stable enough for Claude to continue from the approved plan instead of re-orienting.
- Files: docs/agent-handoff/tasks/second-brain-os-project-0.md, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/settings.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/core/db.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/agents/github_agent.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/orchestration/pipeline.py, .worktrees/second-brain-os-project-0/projects/second-brain-os/src/second_brain/cli/main.py, second-brain/Portfolio/04-Resources/repos/2026-04-19-local-obsidian-daily-agent.md
- Commands: .venv/bin/python -m pytest tests/unit -q, .venv/bin/sbo vault setup, first live artifact written into second-brain/Portfolio/04-Resources/repos
- Blockers: Implementation is in the isolated worktree and has not been merged or committed yet., Current summarization is still intentionally simple; richer summary quality is the next visible improvement.
- Next: Claude should continue from the current Project #0 baseline in the isolated worktree, using the approved Second Brain OS spec/plan and the task file as source of truth. Recommended next implementation slice: improve summarization quality, then expand toward the next source type or broader pipeline/run logging from the approved plan.

### 2026-04-19 - claude-sonnet-4-6 (CURRENT HANDOFF TO CODEX)

- Summary: Major implementation session — expanded Project #0 from a minimal GitHub-only vertical slice to a near-complete production harness. Added real Claude-powered summarization via `core/llm_client.py` (AsyncAnthropic + OpenRouter fallback + cost tracking), `processing/summarizer.py` (YAML prompt loading, section parsing), `processing/context_budget.py` (tiktoken-based token enforcement before every API call), `processing/project_mapper.py` (keyword-based portfolio project matching), three new agents (YouTubeAgent, WebAgent, RSSAgent), two new vault writers (DailyNoteWriter, IndexUpdater/pipeline-log), an async pipeline with `asyncio.gather` for parallel agent execution and per-agent failure isolation, full CLI expansion (sbo add github/youtube/feed/web, sbo status, sbo config), portfolio config YAML (all 24 projects), prompts YAML for repo/video/article, Makefile, .env.example, README.md. All existing tests fixed for the new async pipeline; 14 new test files; 42/42 passing. Lint clean via ruff.
- Files: src/second_brain/core/llm_client.py, src/second_brain/core/models.py, src/second_brain/core/db.py, src/second_brain/processing/summarizer.py, src/second_brain/processing/context_budget.py, src/second_brain/processing/project_mapper.py, src/second_brain/agents/youtube_agent.py, src/second_brain/agents/web_agent.py, src/second_brain/agents/rss_agent.py, src/second_brain/vault/daily_note.py, src/second_brain/vault/index_updater.py, src/second_brain/orchestration/pipeline.py, src/second_brain/cli/main.py, config/sources.yaml, config/portfolio_projects.yaml, prompts/summarize_repo.yaml, prompts/summarize_video.yaml, prompts/summarize_article.yaml, Makefile, .env.example, README.md, pyproject.toml, tests/unit/test_*.py (14 files)
- Commands: UV_CACHE_DIR=$TMPDIR/uv-cache uv sync --extra dev, .venv/bin/python -m pytest tests/unit -q (42 passed), .venv/bin/ruff check src/ tests/ (lint clean)
- Blockers: Implementation is in worktree, not yet merged or committed to main. Real-network ingestion (actual GitHub clone, YouTube transcript, RSS fetch) untested — unit tests use mocks and fake agents. First live run requires ANTHROPIC_API_KEY in .env.
- Next: 1. Commit the worktree branch. 2. Do a first real live run `sbo run` with ANTHROPIC_API_KEY set to validate end-to-end. 3. Phase 2 items from spec: sbo fetch --url (force re-fetch with diff detection), sbo ask (FTS5 search + Claude synthesis), model routing per task type (Haiku for classification), MCP server exposing vault tools. 4. LaunchAgent setup script for 7am daily automation.


### 2026-04-19 - claude-sonnet-4-6 (HANDOFF TO CODEX)

- Summary: Major workspace cleanup + architecture decision session. SBO now has a working Mac app, async pipeline, real Claude summarization, 42 passing tests. Today: cleaned the entire workspace (deleted second-brain/, obsidian-daily-agent, kalshi bots kept by user), consolidated to ONE vault at Brain/, added PORTFOLIO.md (24-project source of truth), rewrote AGENTS.md (setup instructions for Claude Code, Cursor, VS Code, Codex), reset git history with fresh init. Key architecture decision: SBO needs to evolve from a dumb ingestion pipeline into a smart personal research agent.

- Files changed this session:
  - `/Volumes/VeN/Claude-Code-Work/PORTFOLIO.md` — CREATED: full 24-project spec, build order, standards
  - `/Volumes/VeN/Claude-Code-Work/AGENTS.md` — REWRITTEN: setup instructions for all tools
  - `/Volumes/VeN/Claude-Code-Work/CLAUDE.md` — updated vault path to Brain/
  - `/Volumes/VeN/Claude-Code-Work/Brain/` — cleaned junk files (HEARTBEAT, SOUL, IDENTITY, TOOLS, USER, kalshi API note)
  - `/Volumes/VeN/Claude-Code-Work/Brain/02-Projects/` — CREATED: 25 portfolio project subfolders (00-24)
  - `.worktrees/.../config/sources.yaml` — removed HN RSS feed
  - `.worktrees/.../src/second_brain/core/settings.py` — VAULT_PATH updated to Brain/
  - `.worktrees/.../src/second_brain/app/mac_app.py` — VAULT_PATH updated to Brain/, "▶ Run All" header button added
  - `.worktrees/.../src/second_brain/app/static/index.html` — UI: always-visible Run All button, better error feedback, setBusy() helper
  - `.worktrees/.../projects/second-brain-os/.env` — VAULT_PATH updated to Brain/

- Commands run: sbo-app (Mac app running, PID 42749), Brain cleanup, git reinit

- Blockers:
  - `rm -rf Brain/.git` needs to be run from Terminal (sandbox blocked). Then `git add Brain/ && git commit -m "init: clean workspace"` to finish the fresh git.
  - `rm -rf /Volumes/VeN/Claude-Code-Work/second-brain` — user may or may not have run this yet, verify.
  - SBO worktree NOT merged to main yet (branch: chore/seed-obsidian-agent-workspace). Still lives in .worktrees/second-brain-os-project-0/projects/second-brain-os/

- Architecture decision (IMPORTANT — read before touching SBO):
  Venki decided the current SBO pipeline is "not efficient" — it's a dumb push pipeline. The agreed direction is to rebuild it as a smart personal research agent. Architecture (from GPT Researcher + STORM + Perplexica research):

  ```
  sbo research "context window engineering"
       ↓
  ProjectContext        ← reads PORTFOLIO.md, knows current project spec
       ↓
  QueryDecomposer       ← generates 3-5 sub-questions
       ↓
  ┌────┴────┐
  VaultSearch  WebFetch  ← parallel asyncio.gather, vault FIRST
  (ChromaDB)  (httpx)
  └────┬────┘
       ↓
  ChunkReranker         ← semantic similarity, keep top-K
       ↓
  Synthesizer           ← partial summary
       ↓
  GapAnalyzer ──────→ (gaps exist, depth<2?) → loop back
       ↓
  ReportWriter          → Brain/02-Projects/[project]/research.md

  Exposed as MCP stdio server:
    search_vault(query)     ← Claude Code calls this mid-session
    deep_research(topic)    ← full loop above
    project_brief(name)     ← "what do I know about ContextForge?"
  ```

  Stack: LangGraph + ChromaDB (embed Brain/ notes) + httpx + Anthropic SDK + MCP Python SDK
  Interface: pure CLI (no Mac app needed for this). Mac app can stay for adding links.

- Next action options for Codex (pick one):
  1. **OPTION A — Build the research agent** (recommended if 2+ hours available):
     - Add ChromaDB to SBO: `uv add chromadb sentence-transformers`
     - Create `src/second_brain/vault/index.py` — VaultIndex class that embeds Brain/ markdown files
     - Create `src/second_brain/research/agent.py` — LangGraph graph with the loop above
     - Create `src/second_brain/mcp_server.py` — MCP stdio server exposing 3 tools
     - CLI: `sbo research "topic"` + `sbo ask "question"`
     - Test: `sbo research "context window engineering"` → research.md in Brain/02-Projects/01-ContextForge/

  2. **OPTION B — Start Portfolio Project #01 ContextForge** (if starting fresh is cleaner):
     - `mkdir projects/01-contextforge && cd projects/01-contextforge && uv init`
     - Follow PORTFOLIO.md → Project 01 spec (ContextEngine, SemanticScorer, BudgetAllocator, CompressionEngine)
     - Benchmark target: HotpotQA, 40%+ cost reduction, RAGAS faithfulness > 0.84
     - This is the highest-signal project in the portfolio

  3. **OPTION C — Finish SBO basics first** (if you want to close it out before moving on):
     - `sbo ask "query"` — FTS5 search over Brain/ + Claude synthesis (no LangGraph needed, simpler)
     - LaunchAgent script at `scripts/setup_launchagent.sh` for 7am daily automation
     - Merge worktree to main: `git merge chore/seed-obsidian-agent-workspace`

- Vault location: `/Volumes/VeN/Claude-Code-Work/Brain/` (single source of truth)
- SBO worktree: `/Volumes/VeN/Claude-Code-Work/.worktrees/second-brain-os-project-0/projects/second-brain-os/`
- Portfolio spec: `/Volumes/VeN/Claude-Code-Work/PORTFOLIO.md`

### 2026-04-19 - codex

- Summary: Committed the clean Second Brain OS baseline into the main workspace under `projects/second-brain-os` and stopped relying on the broken ignored `.worktrees` git metadata. Added vault-first semantic search foundation: `sbo index`, `sbo ask`, ChromaDB persistent vector store, EmbeddingGemma default with MiniLM fallback, indexed-file hash tracking, and unit coverage. Verified Hugging Face access for `google/embeddinggemma-300m`; real smoke indexing against `Brain/` produced 18 files and 315 chunks with temporary state. Added local ignores for old unrelated project folders and local tool folders to keep workspace status clean without deleting user files.
- Files: projects/second-brain-os/, docs/superpowers/plans/2026-04-19-sbo-vault-semantic-search.md, .gitignore, docs/agent-handoff/ACTIVE_TASKS.md, docs/agent-handoff/tasks/second-brain-os-project-0.md
- Commands: uv sync --extra dev, .venv/bin/python -m pytest tests/unit -q, .venv/bin/ruff check src/ tests/, EMBEDDING_MODEL=google/embeddinggemma-300m EMBEDDING_TRUNCATE_DIM=128 .venv/bin/sbo index, git commit -m "feat: add second brain os semantic search"
- Blockers: Live `sbo ask` has not been run because it calls Claude and spends tokens. Brain is currently tracked as a git submodule entry in the root repo, so vault content changes do not appear as normal file diffs from this repo.
- Next: Implement `sbo research "context window engineering"` with LangGraph: load project context from PORTFOLIO.md, decompose questions, search vault first, fetch external gaps, synthesize cited report, and write `Brain/02-Projects/01-ContextForge/research.md`.
