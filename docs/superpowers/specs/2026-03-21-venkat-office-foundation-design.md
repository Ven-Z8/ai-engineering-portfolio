# Venkat's AI Engineering Office — Foundation Design
**Date:** 2026-03-21
**Scope:** Option B — CLAUDE.md + Workspace Structure
**Status:** Approved

---

## 1. Context & Problem

**Problem:** No execution environment. Working in Cursor chat with no structure, no accountability, no office feeling. Prototypes get built in an hour, then two days of drift.

**Goal:** A Mac Mini workspace that feels like a real office — structured, agentic, disciplined. Foundation strong enough to grow departments, tools, and a second brain on top of.

**Design Principle:** Future-proof. Every decision made tonight should be addable-to, not replaceable.

---

## 2. Workspace Structure

```
/Volumes/VeN/Claude-Code-Work/
│
├── CLAUDE.md                          ← Master config — the office constitution
│
├── .claude/
│   ├── agents/                        ← Department subagents (native Claude Code location)
│   └── commands/                      ← Slash commands
│
├── second-brain/
│   ├── inbox/
│   │   ├── docs/                      ← API docs, official documentation drops
│   │   ├── articles/                  ← Blog posts, tutorials, research papers
│   │   ├── screenshots/               ← Images, UI references, diagrams
│   │   └── urls.md                    ← Quick URL drops with one-line context
│   ├── knowledge/
│   │   ├── ai-ml/                     ← LLMs, agents, training, evals
│   │   ├── backend/                   ← FastAPI, Python patterns, DBs
│   │   ├── frontend/                  ← TypeScript, React, Next.js
│   │   ├── tools/                     ← Claude Code, MCPs, dev tools
│   │   ├── devops/                    ← Infra, deployment, containers, CI/CD
│   │   └── misc/                      ← True catch-all; move to real category after 2 weeks
│   └── INDEX.md                       ← Searchable master index (auto-updated)
│
├── departments/                       ← Per-department BRIEF.md files (owner-written, agent-read)
│   ├── architect/
│   │   └── BRIEF.md                   ← Stack decisions, active architectural choices
│   ├── backend/
│   │   └── BRIEF.md
│   ├── frontend/
│   │   └── BRIEF.md
│   ├── ml-engineer/
│   │   └── BRIEF.md
│   ├── tester/
│   │   └── BRIEF.md
│   ├── product-manager/
│   │   └── BRIEF.md
│   ├── researcher/
│   │   └── BRIEF.md
│   ├── ai-engineer/
│   │   └── BRIEF.md
│   └── prompt-engineer/
│       └── BRIEF.md
│
├── tools/                             ← Internal tools built on top of knowledge base
│
├── docs/                              ← Design specs, plans, documentation
│   └── superpowers/
│       └── specs/
│
└── projects/                          ← All actual project work goes here
    └── (project-name)/                ← Each project = its own git repo
```

**Workspace Root Git Strategy:**
The workspace root (`/Volumes/VeN/Claude-Code-Work/`) is a single git repo with a `.gitignore` that excludes `projects/` (each project is its own nested repo). The second brain, agents, CLAUDE.md, and department briefs are all version-controlled at the workspace level. This means changes to the office itself are tracked.

---

## 3. CLAUDE.md Structure

The CLAUDE.md is the **constitution of the office**. All agents, all sessions, all projects inherit from it. Only the owner (Venkat) can modify it — no agent may edit CLAUDE.md without explicit owner instruction.

### Sections

**1. Identity**
- Owner: Venkat — AI Engineer
- Stack: Python/FastAPI, TypeScript/React/Next.js, Anthropic SDK, LangChain/LangGraph, Claude Agent SDK
- Workspace root: `/Volumes/VeN/Claude-Code-Work`

**2. Behavioral Rules (inherited by ALL agents)**
- Ask before: creating new files/directories, architectural decisions, anything touching external APIs or incurring costs
- Run freely: reading, editing existing files, running tests, local terminal commands
- Always ask: before deleting, pushing to git, deploying, making calls that cost money
- Never: use OpenAI. Always: Anthropic.
- Never: modify CLAUDE.md without explicit owner instruction.

**3. Department Roster**

| Department | Agent | Invoke when... | Tight trigger description |
|---|---|---|---|
| Architect | `@architect` | System design, tech decisions, cross-dept impact | "Use when designing new systems, evaluating tech stack choices, reviewing inter-service communication, or when a decision affects more than one department" |
| Backend | `@backend-developer` | FastAPI routes, Python scripts, DB schemas | "Use when building or debugging Python/FastAPI endpoints, database schemas, background tasks, or server-side scripts" |
| Frontend | `@frontend-developer` | TypeScript, React/Next.js work | "Use when working on TypeScript, React, Next.js, UI components, or browser-side logic — explain choices clearly as owner is learning frontend" |
| ML Engineer | `@ml-engineer` | Model training, pipelines, notebooks | "Use when working on model training, evaluation pipelines, Jupyter notebooks, feature engineering, or MLOps" |
| Tester | `@tester` | Writing tests, QA | "Use when writing unit/integration tests, reviewing coverage gaps, setting up CI test runs, or auditing test quality" |
| Product Manager | `@product-manager` | Scope, priorities, roadmap | "Use when making feature scope decisions, prioritizing work, defining MVP boundaries, or writing product specs" |
| Researcher | `@researcher` | Gather info, summarize docs | "Use when exploring an unknown topic, summarizing documentation, comparing tools/libraries, or gathering background information before building" |
| AI Engineer | `@ai-engineer` | Agent systems, LLM integration | "Use when building multi-agent systems, LangChain/LangGraph pipelines, Anthropic SDK integrations, or Claude Agent SDK workflows" |
| Prompt Engineer | `@prompt-engineer` | Prompt design, evals | "Use when designing or optimizing system prompts, running evals, improving LLM output quality, or debugging prompt behavior" |

**Agent Handoff Protocol:**
When an agent reaches the boundary of its role, it must surface the handoff explicitly:
> "This requires @architect input — I'm stopping here. Recommend invoking @architect with: [specific question]."

Agents do NOT silently continue into another department's domain. They stop, name the right agent, and give the owner a clear handoff prompt.

**4. Stack Conventions**
- Python: `pip + venv` (transitioning to `uv` on new projects — use `uv` for all new project setups)
- Common commands: `python -m pytest`, `uvicorn app.main:app --reload`
- New models: provide documentation before introducing to workspace
- AI frameworks: Anthropic SDK, LangChain/LangGraph, Claude Agent SDK

**5. Second Brain Protocol**
- Drop resources in: `second-brain/inbox/`
- Reference knowledge from: `second-brain/knowledge/`
- Always check `second-brain/INDEX.md` before starting any research task
- Run `/process-inbox` to process new drops

**6. Project Protocol**
- All projects under: `projects/`
- Each project gets its own git repo
- README required before first commit

**7. Cost & Token Rules**
- Default model: Sonnet
- Opus: only for `@architect` on system design, `@ai-engineer` on agent architecture decisions
- Thinking tokens: set per-agent in frontmatter, not globally
- Keep active MCP servers under 10

**8. CLAUDE.md Changelog**
```
## Changelog
2026-03-21 — Initial version. Foundation setup.
```

---

## 4. Department Agents

### Source Strategy
- Base: VoltAgent/awesome-claude-code-subagents (127 pre-built agents, ~80% reuse)
- Override: Customize each agent with Venkat's stack, anti-OpenAI rule, department roster awareness, handoff protocol
- Location: `.claude/agents/` (native Claude Code agent discovery path)

### Agent Format
```markdown
---
name: <agent-name>
description: <tight, specific trigger conditions — this is what Claude uses for auto-routing>
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet | opus
---

[Customized system prompt]
```

### Department Mapping

| Department | Base Agent (VoltAgent) | Category | Model |
|---|---|---|---|
| Architect | `microservices-architect.md` | 01-core-development | opus |
| Backend | `backend-developer.md` | 01-core-development | sonnet |
| Frontend | `frontend-developer.md` | 01-core-development | sonnet |
| ML Engineer | `machine-learning-engineer.md` | 05-data-ai | sonnet |
| Tester | `qa-engineer.md` | 04-quality-security | sonnet |
| Product Manager | `product-manager.md` | 08-business-product | sonnet |
| Researcher | `research-analyst.md` | 10-research-analysis | sonnet |
| AI Engineer | `ai-engineer.md` | 05-data-ai | opus |
| Prompt Engineer | `prompt-engineer.md` | 05-data-ai | sonnet |

### Key Customizations Per Agent
1. Stack override: Python/FastAPI (not Node.js/Go for backend agents)
2. Anthropic-first: never suggest OpenAI
3. Dept roster: each agent knows all 9 departments and their trigger conditions
4. Handoff protocol: surface handoff explicitly, never silently cross boundaries
5. Behavioral rules: inherits ask-first + trust-middle from CLAUDE.md
6. Read `departments/<name>/BRIEF.md` at start of every task for current context

### Department BRIEF.md Format
Each `departments/<name>/BRIEF.md` is written by the owner, read by the agent:
```markdown
# [Department Name] Brief
Last updated: YYYY-MM-DD

## Active Stack Decisions
- [decision] — [reason]

## Current Context
- [what this department is working on]

## Known Constraints
- [limitations, blockers, preferences]
```

---

## 5. Second Brain

### Design Philosophy
Zero-friction intake. Drop anything into `inbox/` — no organizing required at time of input. A slash command (`/process-inbox`) handles categorization, moving, and index updates.

### Intake Protocol
1. Drop resource into appropriate `inbox/` subfolder (docs, articles, screenshots, urls.md)
2. Run `/process-inbox` — Claude reads, categorizes, moves to `knowledge/`, updates `INDEX.md`
3. Before any research: check `INDEX.md` first

### `/process-inbox` Command Behavior
- **Input:** scans all files in `second-brain/inbox/` (all subfolders)
- **Categorization:** LLM-based — reads content, assigns to one of: `ai-ml/`, `backend/`, `frontend/`, `tools/`, `devops/`, `misc/`
- **File handling:** moves (not copies) files from `inbox/` to `knowledge/<category>/`
- **Screenshots:** moved to `knowledge/<category>/` with an auto-generated `.md` description file alongside
- **Conflict handling:** if file with same name exists, appends `-YYYY-MM-DD` suffix
- **INDEX.md update:** appends new entries in format below; never rewrites existing entries
- **URLs (urls.md):** each URL line is fetched, summarized, saved as a `.md` file in appropriate category, original URL line cleared

### INDEX.md Format
```markdown
# Knowledge Base Index
Last updated: YYYY-MM-DD

## AI/ML
- [topic] — brief description — `knowledge/ai-ml/filename.md` — added: YYYY-MM-DD

## Backend
- [topic] — brief description — `knowledge/backend/filename.md` — added: YYYY-MM-DD
```

### Future Tools (Phase 2)
- Vector search over knowledge base (semantic retrieval)
- `/ask-brain "query"` — search knowledge base in natural language
- Screenshot OCR pipeline (extract text from dropped images)
- URL auto-summarizer (paste URL → summary saved to knowledge base)
- INDEX.md → vector DB migration (INDEX.md becomes legacy at this point)

---

## 6. Future-Proofing Notes

- `.claude/agents/` supports unlimited agents — add departments as needed
- `departments/<name>/BRIEF.md` evolves independently of the agent definition
- Second brain `knowledge/` categories can expand without breaking intake protocol
- CLAUDE.md sections are modular — update any section without touching others
- VoltAgent base agents can be swapped as better sources emerge
- Telegram integration: planned as future layer on top of this foundation (not in scope tonight)

---

## 7. Out of Scope (Tonight)

- Telegram bot / group member integration
- Vector DB / semantic search on second brain
- Internal tools (Phase 2)
- Individual project setups
- MCP server configuration
- Hooks and automation scripts

---

## 8. Success Criteria

Build order matters — each step depends on the previous:

- [ ] 1. Workspace root git init + `.gitignore` created
- [ ] 2. All directories scaffolded (`.claude/agents/`, `.claude/commands/`, `second-brain/`, `departments/`, `tools/`, `projects/`)
- [ ] 3. CLAUDE.md written and live
- [ ] 4. Second brain `INDEX.md` stub created, all intake folders ready
- [ ] 5. All 9 `departments/<name>/BRIEF.md` stubs created
- [ ] 6. All 9 department agents in `.claude/agents/` — customized from VoltAgent base
- [ ] 7. `/process-inbox` slash command created in `.claude/commands/`
- [ ] 8. Workspace feels like an office, not a blank terminal

---

## Changelog
- 2026-03-21 — Initial version. Foundation design. Reviewed and updated after spec review.
