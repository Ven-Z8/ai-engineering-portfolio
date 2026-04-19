# Venkat's AI Engineering Office
> This is the master context file. Every Claude session, every agent, every project inherits these rules.
> Last updated: 2026-03-21

---

## 1. Identity & Mission

I am Venkat — an AI Engineer building real-world, impactful AI systems.
This workspace is my office. Not a playground. Not a learning sandbox. A place where things get built and shipped.

**Primary focus:** AI systems, agent architectures, LLM-powered products.
**Working style:** Bias toward execution. Ugly working code beats clean unused code.
**Stack:** Python/FastAPI backend, TypeScript/Next.js frontend, Anthropic SDK, LangChain/LangGraph, Claude Agent SDK.

---

## 2. Behavioral Rules (All Agents Inherit These)

### Ask First — before any of these:
- Creating new files or directories outside existing project structure
- Making architectural decisions that affect multiple components
- Any external API calls that cost money or have rate limits
- Installing new packages or dependencies
- Any action involving git push, deploy, or production systems

### Run Freely — no confirmation needed for:
- Reading any file in the workspace
- Editing existing files (non-destructive changes)
- Running tests locally
- Running local dev servers
- Searching, grepping, globbing the codebase

### Always Ask — hard stops:
- Deleting files or directories
- Git force push or reset --hard
- Any action that cannot be easily undone
- Spending money (API calls with significant token cost)
- Touching `.env` files or secrets

---

## 3. Department Roster

When a task clearly belongs to a department, route to that agent.
Do NOT try to do everything yourself — delegate.

| Agent | File | Trigger When... |
|---|---|---|
| `architect` | `.claude/agents/architect.md` | System design, tech stack decisions, component planning, architecture reviews |
| `backend` | `.claude/agents/backend.md` | FastAPI routes, Python scripts, DB schemas, REST APIs, background tasks |
| `frontend` | `.claude/agents/frontend.md` | TypeScript, React, Next.js — always explain clearly, owner is learning frontend |
| `ml-engineer` | `.claude/agents/ml-engineer.md` | Model training, ML pipelines, Jupyter notebooks, data processing, MLOps |
| `tester` | `.claude/agents/tester.md` | Writing tests, coverage analysis, QA review, debugging failing tests |
| `product-manager` | `.claude/agents/product-manager.md` | Scope decisions, feature prioritization, MVP definition, roadmap planning |
| `researcher` | `.claude/agents/researcher.md` | Gathering information, summarizing docs/papers, exploring new tools |
| `ai-engineer` | `.claude/agents/ai-engineer.md` | Agent systems, LangChain/LangGraph pipelines, Anthropic SDK, Claude Agent SDK |
| `prompt-engineer` | `.claude/agents/prompt-engineer.md` | Prompt design, system prompts, evals, optimization, model behavior tuning |

---

## 4. Stack Conventions

### Python
- **Package manager:** `pip` + `venv` for existing projects. `uv` for all new projects.
- **New project setup:** `uv init`, `uv add <package>`, `uv run <command>`
- **Test runner:** `python -m pytest` or `uv run pytest`
- **API server:** `uvicorn app.main:app --reload`
- **Linting:** `ruff check .` — always run before considering code done
- **Type hints:** Required on all function signatures
- **Env vars:** Always use `python-dotenv`, never hardcode secrets

### TypeScript / Frontend
- **Framework:** Next.js (App Router preferred) or plain React
- **Package manager:** `npm` or `pnpm`
- **Styling:** Tailwind CSS preferred
- **Note:** Frontend is NOT Venkat's strength — agents must explain frontend decisions clearly, suggest the simplest possible approach, avoid over-engineering

### AI / LLM
- **Primary SDK:** Anthropic Python SDK (`anthropic`)
- **Agent framework:** Claude Agent SDK for multi-agent systems
- **Orchestration:** LangChain/LangGraph for complex pipelines
- **NEVER use:** OpenAI SDK — this is a hard rule, no exceptions
- **Other models:** Can be used if docs are provided in session context first
- **Default model:** Claude Sonnet (use Opus only when explicitly required)
- **Token budget:** Cap thinking tokens at 10,000 unless instructed otherwise

### Git
- **Branching:** `main` = stable, feature branches for new work
- **Commits:** Descriptive messages, conventional commits format preferred
- **Never:** Force push to main

---

## 5. Second Brain Protocol

The knowledge base (Obsidian vault) lives at `Brain/`. OpenClaw writes to it. Claude Code reads from it.

### Dropping new resources:
**Single vault:** `Brain/` at `/Volumes/VeN/Claude-Code-Work/Brain/` — open in Obsidian.

### Adding resources for a portfolio project:
1. Drop the link into the Second Brain OS app (sbo-app) → Add Links tab
2. Or run `sbo add github <url>` / `sbo add youtube <url>` from CLI
3. Run `sbo run` — Claude summarizes and writes the note to `Brain/`

### Before researching anything:
- Search `Brain/` first (grep or Obsidian search)
- If it's already there, use it — don't re-fetch what we already have

### Vault categories:
- `Brain/ai-frameworks/` — LangChain, LangGraph, Anthropic SDK, Claude Agent SDK
- `Brain/resources/` — official docs, API references, articles
- `Brain/learning/` — tutorials, walkthroughs, lessons learned
- `Brain/projects/` — general project notes
- `Brain/02-Projects/` — your 24 portfolio builds (one subfolder per project)
- `Brain/ideas/` — raw ideas, hypotheses, concepts
- `Brain/logs/` — daily logs, decisions, experiments

---

## 6. Project Protocol

All real projects live under `projects/`. Each project is its own thing.

### Starting a new project:
1. Run `/new-project` command
2. Architect agent reviews the plan first
3. Create `projects/<project-name>/` directory
4. `README.md` must exist before first commit
5. `.env.example` required if any env vars are used

### Project structure (Python/FastAPI):
```
projects/<name>/
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   └── models/
├── tests/
├── .env.example
├── pyproject.toml (if uv) or requirements.txt
└── README.md
```

### Project structure (Next.js):
```
projects/<name>/
├── src/
│   ├── app/
│   ├── components/
│   └── lib/
├── .env.example
├── package.json
└── README.md
```

---

## 7. Plugin System

Domain-specific skills live under `plugins/`. Each plugin has agents, commands, and skills.

| Plugin | Path | Purpose |
|---|---|---|
| `llm-application-dev` | `plugins/llm-application-dev/` | LangChain, LangGraph, RAG, evals, embeddings |
| `python-development` | `plugins/python-development/` | Python patterns, FastAPI, async, testing |
| `frontend-dev` | `plugins/frontend-dev/` | React, Next.js, TypeScript, Tailwind |
| `agent-orchestration` | `plugins/agent-orchestration/` | Multi-agent coordination, conductor patterns |

New plugins can be added as new domains are introduced. Add entry to this table when adding a plugin.

---

## 8. Cost & Resource Rules

- **Default model:** Claude Sonnet — fast, capable, cost-effective
- **Use Opus when:** Complex architecture decisions, security reviews, critical system design
- **Use Haiku when:** Simple code generation from clear specs, repetitive tasks, fast lookups
- **Max active MCP servers:** 10
- **Cap thinking tokens:** 10,000 per request (override only when explicitly needed)
- **Before long agent runs:** Confirm estimated token usage with Venkat

---

## 9. Execution Principles

These apply to every session, every task:

1. **Action over discussion** — build first, refine later
2. **Ugly working code beats clean unused code**
3. **Test early** — run something visible within the first hour
4. **One idea at a time** — if scope creeps, call it out and lock focus
5. **Real usefulness over technical complexity** — would a real user use this right now?
6. **If stuck for more than 15 minutes** — reduce complexity, don't add more

---

## 10. Session Startup Checklist

At the start of every session:
- [ ] Check `second-brain/INDEX.md` for relevant existing knowledge
- [ ] Confirm which project we're working on
- [ ] Confirm which department agent(s) will be involved
- [ ] State the ONE goal for this session

---

*This file is the source of truth. When in doubt, refer back here.*
