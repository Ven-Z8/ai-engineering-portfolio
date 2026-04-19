# Venki's AI Engineering Workspace
## How to Use This Setup — Claude Code, Cursor, VS Code, Codex

---

## What This Is

This is Venki's AI engineering office. 24 portfolio projects, 10 weeks, targeting Apple/enterprise AI roles.

**Single source of truth files — read these at the start of every session:**
- `CLAUDE.md` — workspace rules, conventions, stack
- `PORTFOLIO.md` — all 24 projects, specs, build order, standards

**Vault:** `Brain/` — the Obsidian knowledge base. All research notes land here.  
**Projects:** `projects/` — one folder per portfolio build.  
**Research CLI:** `sbo` — ingests sources, writes to Brain/ (see below).

---

## Session Start Checklist (any tool)

1. Read `PORTFOLIO.md` — know which project we're on and its spec
2. Read `Brain/02-Projects/<current-project>/` — what research already exists
3. Read `CLAUDE.md` — stack conventions and rules
4. State the ONE goal for the session

---

## Using From Claude Code

Claude Code is the primary builder. It has full access to all tools.

```bash
# Start a session
claude  # opens in this workspace

# Key commands
sbo run                          # ingest all sources → Brain/
sbo add github <url>             # add a GitHub repo to track
sbo add youtube <url>            # add a YouTube video
sbo ask "how does X work"        # search vault + synthesize (coming soon)
```

Claude Code reads `CLAUDE.md` automatically. Feed `PORTFOLIO.md` when starting a new project build.

---

## Using From Cursor

1. Open `/Volumes/VeN/Claude-Code-Work` as workspace root in Cursor
2. At session start, paste into chat:
   ```
   Read PORTFOLIO.md and CLAUDE.md. We're building [project name].
   Check Brain/02-Projects/[project-folder]/ for existing research.
   ```
3. Cursor Agent can run terminal commands — use `sbo run` to refresh the vault

**Cursor settings:**
- Model: claude-sonnet-4-6 (claude-opus-4-7 for architecture decisions)
- Always include `PORTFOLIO.md` and `CLAUDE.md` as context

---

## Using From VS Code (Continue or Cline)

**With Continue:**
```
@file PORTFOLIO.md @file CLAUDE.md
We're building [project name]. Check Brain/02-Projects/[folder]/ for research.
```

**With Cline:**
- Set system prompt to contents of `CLAUDE.md`
- Feed `PORTFOLIO.md` at session start
- Cline can call `sbo` CLI directly through its terminal tool

---

## Using From Codex CLI

```bash
codex "$(cat CLAUDE.md)" "$(cat PORTFOLIO.md)"
# Then:
codex "We're building ContextForge (Project #01). Check Brain/02-Projects/01-ContextForge/ for research."
```

Note: Codex is fine as the IDE tool. All project LLM calls go through Anthropic SDK — never OpenAI SDK in project code (see CLAUDE.md).

---

## Research Workflow

Before building any project:

```bash
# 1. Add relevant sources
sbo add github https://github.com/relevant/repo
sbo add youtube https://youtu.be/relevant-video

# 2. Run ingestion (Claude summarizes → writes to Brain/)
sbo run

# 3. Check what landed
ls Brain/02-Projects/01-ContextForge/

# 4. Build with context already in vault
```

**Research agent (coming soon — MCP server):**
```bash
sbo research "context window engineering"
# → decomposes topic, searches vault + web, writes research brief

# MCP tools Claude Code can call mid-session:
search_vault(query)      # semantic search over Brain/
deep_research(topic)     # full loop: decompose → fetch → rerank → synthesize
project_brief(name)      # "what do I know about ContextForge?"
```

---

## New Project Convention

```bash
mkdir projects/01-contextforge
cd projects/01-contextforge
uv init
```

Every project requires: `CLAUDE.md`, `README.md`, `pyproject.toml`, `Makefile`, `Dockerfile`, `.env.example`, `scripts/benchmark.py`, `tests/evals/`

Full spec in `PORTFOLIO.md` → Universal Engineering Standards section.

---

## Vault Structure

```
Brain/
├── ai-frameworks/     ← LangGraph, Anthropic SDK, MCP, etc.
├── resources/         ← docs, papers, API references
├── learning/          ← tutorials, lessons learned
├── ideas/             ← raw ideas, hypotheses
├── templates/         ← note templates
└── 02-Projects/       ← one subfolder per portfolio project
    ├── 00-Second-Brain-OS/
    ├── 01-ContextForge/
    └── ... (24 total)
```

Search vault before hitting the web:
```bash
grep -r "token budget" Brain/
sbo ask "token budget"    # semantic search + synthesis (coming soon)
```

---

## Key Paths

| Thing | Path |
|---|---|
| Workspace root | `/Volumes/VeN/Claude-Code-Work/` |
| Vault (Obsidian) | `/Volumes/VeN/Claude-Code-Work/Brain/` |
| Portfolio projects | `/Volumes/VeN/Claude-Code-Work/projects/` |
| Master context | `CLAUDE.md` + `PORTFOLIO.md` |
| Research CLI | `sbo` (Second Brain OS) |

---

*Last updated: April 2026*
