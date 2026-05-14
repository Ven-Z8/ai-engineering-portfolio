# Venkat AI Engineering Portfolio

Production-grade AI systems built through a focused public portfolio sprint.

This repository is the command center for 24 portfolio projects targeting senior AI, ML, and agentic engineering roles. The work emphasizes context engineering, multi-agent orchestration, evaluation systems, retrieval quality, guardrails, and reliable LLM application infrastructure.

## Portfolio Thesis

I build AI systems that are measurable, inspectable, and useful beyond the demo. Every project in this workspace is expected to include clear architecture, reproducible setup, tests or evals, benchmark evidence, and operational notes.

## Current Focus

| Track | Project | Purpose |
| --- | --- | --- |
| Foundation | Second Brain OS | Research ingestion and vault-backed project memory |
| Phase 1 | ContextForge | Context window engineering library |
| Phase 1 | RAGBench Pro | RAG strategy comparison and eval pipeline |
| Phase 1 | AgentOrchestra | Schema-driven multi-agent workflow engine |
| Phase 1 | MemoryOS | Agent memory across working, episodic, and procedural layers |

The full project map lives in [PORTFOLIO.md](PORTFOLIO.md).

## Featured Project

| Project | Status | What it shows |
| --- | --- | --- |
| [NL2SQL Viz](https://github.com/Ven-Z8/nl2sql-viz) | Shipped | Natural-language analytics over a demo SaaS dataset, guarded SQL generation, chart planning, FastAPI backend, and Next.js frontend |

## Engineering Standards

- Python 3.12 with `uv`
- FastAPI for service APIs
- Pydantic models for data contracts
- Anthropic SDK through a single LLM client abstraction
- Structured logging and explicit cost tracking for LLM calls
- Tests, evals, and benchmarks before claiming quality
- Conventional commits and daily progress notes

## Repository Map

```text
.
├── PORTFOLIO.md              # 24-project source of truth
├── CLAUDE.md                 # workspace engineering rules
├── projects/                 # portfolio implementations
├── docs/                     # plans, handoffs, progress notes
├── prompts/                  # shared prompt packs and registries
├── scripts/                  # workspace utilities
└── plugins/                  # local engineering playbooks
```

## Build Cadence

The repository is maintained as a real engineering portfolio:

1. Pick a scoped improvement from the portfolio roadmap.
2. Ship a code, docs, test, eval, benchmark, or CI change.
3. Run the most relevant lightweight verification.
4. Record progress and the next useful task.
5. Commit with a conventional message.

The goal is a visible trail of increasingly strong AI engineering work: practical systems, clear tradeoffs, and evidence that the work runs.
