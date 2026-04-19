# Venki — AI Agentic Engineer | 24 Projects Challenge
# This document is the source of truth for all 24 portfolio projects.
# Feed this to Claude Code at the start of every build session.

---

## WHO I AM

**Name:** Venki  
**Role:** AI Engineer (4 years SWE, 2 years AI Engineering)  
**Stack:** Python, TypeScript, LangGraph, Anthropic SDK, FastAPI, Bun  
**Machine:** Mac Mini  
**Tools:** Claude Code (primary builder), Cursor IDE  
**Goal:** Land a senior AI/ML Engineer role at Apple, enterprise AI teams, or AI-native companies  
**Timeline:** 24 projects across 10 weeks (3-4 per week)  

**My Thesis:**  
> "I build production-grade AI systems that are measurably reliable — not just impressive demos — with a focus on context engineering, agent robustness, and evaluation frameworks that prove quality at every layer."

---

## UNIVERSAL ENGINEERING STANDARDS
## Apply these to EVERY project without exception.

### Python Stack
- Python 3.12, managed with `uv`
- `pyproject.toml` always — NEVER `requirements.txt`
- Full type hints on every function signature
- Pydantic `BaseModel` for all data schemas
- `pydantic-settings` `BaseSettings` for all environment config
- `structlog` for logging — NEVER `print()`
- Async `FastAPI` with specific `HTTPException` types
- All LLM calls through a single `LLMClient` abstraction class
- Token counting via `tiktoken` before every LLM call
- Cost tracking: log `tokens_in`, `tokens_out`, `model`, `cost_usd` per call

### Project Structure (every project gets ALL of these)
```
project-name/
├── CLAUDE.md              # project-specific Claude Code instructions
├── README.md              # follows the README formula below
├── pyproject.toml
├── Makefile               # targets: run, test, bench, lint, docker, demo
├── Dockerfile             # multi-stage: builder + runtime
├── .env.example           # all required env vars, no secrets
├── .github/
│   └── workflows/ci.yml   # lint + test on every push
├── src/<name>/
│   ├── core/              # config, settings, logger
│   ├── api/               # FastAPI routes
│   ├── models/            # Pydantic schemas
│   └── utils/
├── prompts/               # all prompts in .yaml files — never inline
├── scripts/
│   └── benchmark.py       # `make bench` runs this, outputs markdown table
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evals/             # AI-specific eval suite
└── docs/
    ├── architecture.md    # ASCII system diagram
    └── benchmarks.md      # all benchmark results with methodology
```

### README Formula (every project, in this order)
1. One-line hook — what problem, what solution
2. Benchmark table — baseline vs ours, minimum 3 metrics
3. Quick install — 3 lines max
4. Architecture ASCII diagram
5. Real code example — not hello world
6. Evaluation results with reproducibility command

### Git Discipline
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `bench:`
- Every merge to main must pass CI

---

## THE 24 PROJECTS

---

### PHASE 1 — WEEKS 1-2: Context Engineering + Multi-Agent
*The rarest skills. Almost no portfolio projects exist here.*

---

#### PROJECT 01 — ContextForge
**Tagline:** Context Window Engineering Library  
**Status:** To Build  
**Priority:** HIGHEST — leads the portfolio  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
Python library for intelligent context management. Dynamic context selection, semantic compression, token budget allocation, sliding window strategies, and context quality scoring.

**Architecture:**
```
Query → Semantic Scorer → Budget Allocator → Context Assembler → LLM
            ↑                   ↑                    ↑
       Embeddings          Token Counter       Compression Engine
```

**Stack:** Python, Anthropic API, tiktoken, FastAPI, Qdrant  

**Key Classes:**
- `ContextEngine` — main entry point
- `SemanticScorer` — ranks content by relevance to query
- `BudgetAllocator` — distributes token budget across context slots
- `CompressionEngine` — semantic compression to fit content in budget
- `ContextWindow` — the assembled, budget-aware context object

**Benchmark Target:**
| Metric | Baseline | Target |
|--------|----------|--------|
| Cost per 1k queries | $2.40 | < $1.00 |
| RAGAS faithfulness | 0.71 | > 0.84 |
| Context utilization | 38% | > 90% |

**Benchmark dataset:** HotpotQA (500 multi-hop questions)  
**Wow factor:** 40%+ cost reduction with measurably better answer quality  

**JD requirements hit:** Context Engineering, LLM APIs, Production-grade  

---

#### PROJECT 02 — RAGBench Pro
**Tagline:** RAG System with Built-in Eval Pipeline  
**Status:** To Build  
**Priority:** HIGH  
**Difficulty:** HIGH | **Days:** 4  

**What it does:**  
Multi-strategy RAG with side-by-side strategy comparison. Implements: naive RAG, HyDE, multi-query, contextual compression, parent-document retriever. RAGAS + DeepEval integration. Live dashboard.

**Architecture:**
```
Query → Strategy Router → [HyDE | MultiQuery | Compression] → Reranker → LLM
                                                                           ↑
                                                               RAGAS Evaluator (runs on every response)
```

**Stack:** LangGraph, Chroma/Qdrant, RAGAS, DeepEval, FastAPI, React  

**Benchmark Target:**
| Strategy | Faithfulness | Answer Rel | Cost/1k | Latency p95 |
|----------|-------------|------------|---------|-------------|
| Naive RAG | 0.71 | 0.68 | $2.40 | 3.2s |
| HyDE | 0.76 | 0.74 | $3.10 | 4.1s |
| **Ours** | **0.84** | **0.81** | **$0.91** | **1.8s** |

**Benchmark dataset:** MS MARCO, HotpotQA  
**Wow factor:** Live dashboard comparing all strategies in real-time  

**JD requirements hit:** RAG Architectures, Vector Databases, Evaluation Frameworks  

---

#### PROJECT 03 — AgentOrchestra
**Tagline:** Supervisor-Worker Multi-Agent System  
**Status:** To Build  
**Priority:** HIGH  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
LangGraph supervisor with specialized workers: researcher, writer, critic, verifier. Human-in-the-loop checkpoints, persistent state, streaming output. Solves real task: automated competitive intelligence reports.

**Architecture:**
```
User Task → Supervisor Agent
               ├── Researcher Agent (web search + synthesis)
               ├── Writer Agent (structured report generation)
               ├── Critic Agent (fact check + quality score)
               └── Verifier Agent (source validation)
                        ↓
              Human-in-the-Loop Checkpoint
                        ↓
              Final Report → Obsidian Vault
```

**Stack:** LangGraph, Anthropic API, FastAPI, SQLite (persistent state)  

**Benchmark Target:**
- Task completion rate: > 90%
- Report quality score (LLM-as-judge): > 8/10
- End-to-end latency for competitive analysis: < 4 minutes

**Wow factor:** Generates full competitive analysis report from one sentence input  

**JD requirements hit:** LangGraph, Autonomous Agents, Production-grade  

---

#### PROJECT 04 — MemoryOS
**Tagline:** Episodic + Semantic Memory for AI Agents  
**Status:** To Build  
**Difficulty:** MEDIUM | **Days:** 2  

**What it does:**  
Three-tier memory architecture: working memory (current context), episodic memory (past conversations with semantic search), procedural memory (learned behaviors). Agents that demonstrably improve over time.

**Architecture:**
```
Agent ←→ MemoryOS
              ├── Working Memory    (in-context, current session)
              ├── Episodic Memory   (Qdrant — semantic search over past)
              └── Procedural Memory (SQLite — learned patterns + preferences)
```

**Stack:** Python, Qdrant, Anthropic API, Redis, SQLite  
**Wow factor:** Agent demonstrably improves task completion over 10+ interactions  

**JD requirements hit:** Autonomous Agents, RAG Architectures, Context Engineering  

---

#### PROJECT 05 — AutoResearch v2
**Tagline:** Karpathy Loop — Autonomous Overnight Optimizer  
**Status:** Exists (basic research pattern)  
**Difficulty:** MEDIUM | **Days:** 2  

**What it does:**  
Karpathy-style autoresearch agent: generates hypotheses, tests them, logs results, distills findings, iterates. Locked evaluation harness. Runs overnight autonomously. General-purpose research loop.

**Stack:** LangGraph, Claude Code SDK, Anthropic API, SQLite, Rich  
**Wow factor:** Overnight runs producing structured insight reports, zero babysitting  

**JD requirements hit:** Autonomous Agents, AI Governance, Model Lifecycle  

---

### PHASE 2 — WEEK 3: MCP Protocol
*Newest signal in the market. 97M SDK downloads. Almost zero portfolio projects.*

---

#### PROJECT 06 — MCPForge Suite
**Tagline:** 5 Production MCP Servers  
**Status:** To Build  
**Priority:** HIGHEST — most differentiated project in the portfolio  
**Difficulty:** HIGH | **Days:** 4  

**What it does:**  
Suite of 5 hardened, documented MCP servers published to PyPI:
1. `mcp-github` — PR review agent, issue triage
2. `mcp-notion` — knowledge base queries
3. `mcp-linear` — issue management agent
4. `mcp-postgres` — natural language SQL queries
5. `mcp-filesystem` — secure read/write with permission controls

**Architecture:**
```
Any LLM (Claude, GPT-4, Gemini)
    ↓ MCP Protocol
MCPForge Server ←→ [GitHub | Notion | Linear | PostgreSQL | Filesystem]
    ↓
Secure, standardized tool responses
```

**Stack:** Python MCP SDK, FastAPI, GitHub/Notion/Linear APIs, PostgreSQL  
**Target:** Published on PyPI. Real installs. Real usage.  
**Wow factor:** `pip install mcp-github` and any MCP-compatible LLM has GitHub superpowers  

**JD requirements hit:** MCP Protocol, LLM Integration, Production-grade  

---

#### PROJECT 07 — MCPGuard
**Tagline:** Security & Safety Layer for MCP Servers  
**Status:** To Build  
**Priority:** HIGH — only MCP security framework that exists  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
Middleware wrapper for any MCP server:
- PII detection + redaction (Microsoft Presidio)
- Prompt injection detection
- Rate limiting per client
- Audit logging (every request, tamper-proof)
- Access control (which LLMs can call which tools)

**Stack:** Python, Presidio, MCP SDK, Redis  

```python
# Usage — wrap ANY existing MCP server:
from mcpguard import SecureMCP
server = SecureMCP(
    server=your_existing_mcp_server,
    pii_detection=True,
    injection_detection=True,
    audit_log="./audit.log"
)
```

**Wow factor:** The only open-source MCP security framework. Period.  

**JD requirements hit:** MCP Protocol, AI Guardrails, PII/PHI Handling, Safety Controls  

---

### PHASE 3 — WEEK 4: Evaluation + Safety
*Evals are the moat. Senior engineers measure everything.*

---

#### PROJECT 08 — EvalEngine
**Tagline:** LLM-as-Judge Evaluation Framework  
**Status:** To Build  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
From-scratch evaluation suite for any LLM app. Metrics: faithfulness, answer relevance, context precision/recall, groundedness, toxicity, prompt injection robustness. CLI + Python API + dashboard.

```python
from evalengine import Evaluator
evaluator = Evaluator(metrics=["faithfulness", "relevance", "groundedness"])
results = evaluator.evaluate(questions=my_questions, pipeline=my_rag_pipeline)
results.to_markdown()  # → ready for README
```

**Stack:** Python, Anthropic API, FastAPI, React  
**Wow factor:** Outputs structured eval reports with benchmark table ready for README  

**JD requirements hit:** Evaluation Frameworks, AI Governance, Production-grade  

---

#### PROJECT 09 — GuardStack
**Tagline:** AI Guardrails & Content Safety Framework  
**Status:** To Build  
**Difficulty:** MEDIUM | **Days:** 3  

**What it does:**  
Layered guardrails: input validation → prompt injection detection → output filtering → hallucination detection → PII scrubbing → policy enforcement. Integrates with LangChain callbacks and LangGraph nodes.

**Architecture:**
```
User Input → [Input Guard] → LLM → [Output Guard] → User
                  ↓                        ↓
           Injection Check          Hallucination Check
           PII Detection            PII Scrubbing
           Policy Validation        Toxicity Filter
```

**Stack:** Python, Anthropic API, LangGraph, Presidio  
**Wow factor:** Demonstrated catching real jailbreak attempts with benchmark stats  

**JD requirements hit:** AI Guardrails, Content Filtering, Safety Controls, PII/PHI  

---

#### PROJECT 10 — LLMScope
**Tagline:** Observability Dashboard for LLM Applications  
**Status:** To Build  
**Difficulty:** MEDIUM | **Days:** 2  

**What it does:**  
Real-time observability: cost per request/user/feature, latency p50/p95/p99, quality metric trends, prompt drift detection, error rates. Like Datadog but purpose-built for AI systems.

**Stack:** Python, FastAPI, SQLite, React, Recharts  
**Wow factor:** Live cost + quality tradeoff curves in real-time dashboard  

**JD requirements hit:** AI Governance, Model Lifecycle, Production-grade  

---

### PHASE 4 — WEEK 5: Advanced RAG + Knowledge Graphs
*GraphRAG is where most candidates drop off.*

---

#### PROJECT 11 — GraphRAG Engine
**Tagline:** Hybrid Vector + Knowledge Graph RAG  
**Status:** To Build  
**Difficulty:** VERY HIGH | **Days:** 4  

**What it does:**  
Full GraphRAG pipeline: entity extraction → knowledge graph construction → community detection → graph-aware retrieval. Combines Neo4j graph traversal with vector similarity.

**IMPORTANT — Honest benchmark design:**  
GraphRAG does NOT universally beat standard RAG. Build with honest benchmarks showing:
- Where it wins: multi-hop relational queries, dense entity corpora
- Where it loses: simple factual lookups, time-sensitive queries (13-16% accuracy drop)
This nuanced take is a senior signal.

**Architecture:**
```
Documents → Entity Extractor → Knowledge Graph (Neo4j)
                                       ↓
Query → [Vector Search + Graph Traversal] → Hybrid Retriever → LLM
```

**Stack:** Python, Neo4j, Anthropic API, Chroma  
**Benchmark dataset:** GraphRAG-Bench (2026, ICLR accepted)  
**Wow factor:** Side-by-side showing exactly when GraphRAG beats plain RAG and why  

**JD requirements hit:** Knowledge Graphs, GraphRAG, RAG Architectures, Vector DBs  

---

#### PROJECT 12 — PromptOpt
**Tagline:** Automatic Prompt Optimization (DSPy-inspired)  
**Status:** To Build  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
DSPy-inspired framework: define task + metric, run bootstrap few-shot optimization, test-time prompt compilation. Automatically improves prompts using the LLM itself.

**Stack:** Python, Anthropic API, DSPy, FastAPI  
**Wow factor:** Before/after showing optimized prompts outperform hand-written by measurable margin  

**JD requirements hit:** Prompt Engineering, Model Lifecycle, Evaluation  

---

### PHASE 5 — WEEK 6: Structured Tool Use
*Production-grade tool orchestration. Where agent demos fall apart.*

---

#### PROJECT 13 — ToolForge
**Tagline:** Production Tool Use Framework with Error Recovery  
**Status:** To Build  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
Framework for reliable tool use: automatic retry with exponential backoff, partial failure recovery, tool call tracing, fallback chains, cost-aware tool selection.

**Benchmark Target:**
| Condition | Baseline Completion | ToolForge Completion |
|-----------|--------------------|--------------------|
| Normal | 95% | 97% |
| Tool fails 30% of time | 61% | 94% |
| Tool returns bad data | 48% | 89% |

**Stack:** Python, Anthropic API, Pydantic, FastAPI, Redis  
**Wow factor:** 94% task completion vs 61% baseline under adversarial conditions  

**JD requirements hit:** Autonomous Agents, Production-grade, AI Governance, LLM APIs  

---

#### PROJECT 14 — StructOut
**Tagline:** Guaranteed Structured Output Engine  
**Status:** To Build  
**Difficulty:** MEDIUM | **Days:** 2  

**What it does:**  
LLM-agnostic library for guaranteed schema-adherent outputs. Multi-attempt self-correction with schema feedback, confidence scoring per field. Goes beyond `instructor` — adds validation chains and field-level retries.

**Stack:** Python, Anthropic API, Pydantic, FastAPI  
**Benchmark:** 99.7% schema adherence across 10k test cases including adversarial inputs  

**JD requirements hit:** Context Engineering, LLM APIs, Production-grade  

---

#### PROJECT 15 — SemanticRouter
**Tagline:** Intent-Based Query Router for Multi-Chain LLM Apps  
**Status:** To Build  
**Difficulty:** MEDIUM | **Days:** 2  

**What it does:**  
Routes incoming queries to specialized chains/agents based on semantic intent, not keyword matching. Configurable confidence thresholds, A/B routing for experimentation.

**Stack:** Python, FastAPI, Qdrant, Anthropic API, scikit-learn  
**Wow factor:** 3x latency reduction + 40% cost drop by routing simple queries to smaller models  

**JD requirements hit:** Context Engineering, Autonomous Agents, Production-grade  

---

### PHASE 6 — WEEK 7: Doc & Data Intelligence
*Real enterprise AI is mostly document processing.*

---

#### PROJECT 16 — DocIQ
**Tagline:** Intelligent Document Processing Pipeline  
**Status:** To Build  
**Priority:** HIGH — directly targets Apple Legal job posting  
**Difficulty:** HIGH | **Days:** 4  

**What it does:**  
End-to-end IDP pipeline: OCR + layout detection → semantic sectioning → entity extraction → table parsing → metadata enrichment → RAG-ready vector ingestion. Handles PDFs, scanned images, legal contracts, mixed-format archives.

**Architecture:**
```
Document → OCR (Surya) → Layout Detector → Section Extractor
                                                    ↓
                              Entity Extractor → Metadata Enricher
                                                    ↓
                                           Chunker → Embedder → Qdrant
                                                    ↓
                                              Query Interface (FastAPI)
```

**Stack:** Python, Surya, React, Chroma, Anthropic API, FastAPI  
**Wow factor:** 200-page legal contract → queryable knowledge base in < 60 seconds  

**JD requirements hit:** RAG Architectures, Vector Databases, Production-grade, Context Engineering  

---

#### PROJECT 17 — SynthGen
**Tagline:** Synthetic Training & Eval Data Generator  
**Status:** To Build  
**Difficulty:** MEDIUM | **Days:** 3  

**What it does:**  
LLM-powered synthetic data factory: generates Q&A pairs, adversarial examples, edge cases, labeled datasets from any corpus. Includes quality filtering, deduplication, diversity scoring, HuggingFace export.

**Stack:** Python, Anthropic API, HuggingFace Datasets, Pandas, FastAPI  
**Wow factor:** Generated eval dataset that exposed 3 critical RAG failures invisible to manual testing  

**JD requirements hit:** AI Governance, Evaluation Frameworks, Model Lifecycle, RAG Architectures  

---

### PHASE 7 — WEEK 8: Self-Correcting & Adversarial AI
*Agents that break gracefully. Senior-tier thinking.*

---

#### PROJECT 18 — SelfHeal
**Tagline:** Self-Correcting Agent with Failure Detection & Recovery  
**Status:** To Build  
**Priority:** HIGH — most underrepresented skill in AI portfolios  
**Difficulty:** VERY HIGH | **Days:** 4  

**What it does:**  
Agentic loop with built-in self-repair: output validation at each step, automatic error classification (hallucination vs tool failure vs context loss), targeted correction strategies, rollback to last valid checkpoint.

**Architecture:**
```
Task → Agent Loop
    ↓         ↑ (on failure)
  Execute   ↙
    ↓    Diagnose Error
  Validate    ├── Hallucination → Re-prompt with constraints
    ↓         ├── Tool Failure  → Retry with fallback
  Success     ├── Context Loss  → Re-inject context
              └── Unknown       → Rollback to checkpoint
```

**Stack:** LangGraph, Anthropic API, Pydantic, SQLite, FastAPI  
**Wow factor:** Completes a 12-step research task after intentionally injecting 4 failures mid-run  

**JD requirements hit:** Autonomous Agents, AI Governance, LangGraph  

---

#### PROJECT 19 — RedTeamKit
**Tagline:** Adversarial Testing Framework for LLM Applications  
**Status:** To Build  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
Automated red-teaming suite: prompt injection attacks, jailbreak attempt library, data exfiltration probes, role confusion attacks, context manipulation tests. Generates structured vulnerability reports with severity scoring.

**Stack:** Python, Anthropic API, FastAPI, React  
**Wow factor:** Discovered prompt injection vulnerability in real open-source LLM app, responsibly disclosed  

**JD requirements hit:** AI Guardrails, Safety Controls, Content Filtering, AI Governance  

---

### PHASE 8 — WEEK 9: Real-Time AI Systems
*Static RAG is solved. Real-time is the next frontier.*

---

#### PROJECT 20 — LiveRAG
**Tagline:** Streaming Real-Time RAG with Dynamic Index Updates  
**Status:** To Build  
**Difficulty:** HIGH | **Days:** 4  

**What it does:**  
RAG with live data ingestion via webhooks, SSE, APIs. New documents chunked, embedded, indexed in < 2 seconds. Staleness detection, freshness scoring in retrieval ranking, live monitoring dashboard.

**Stack:** Python, Qdrant, FastAPI, WebSockets, Anthropic API, Redis  
**Wow factor:** Answers questions about news published 90 seconds ago with full source context  

**JD requirements hit:** RAG Architectures, Vector Databases, Production-grade, Model Lifecycle  

---

#### PROJECT 21 — SemanticCache
**Tagline:** Semantic Similarity Caching Layer for LLM APIs  
**Status:** To Build  
**Difficulty:** MEDIUM | **Days:** 2  

**What it does:**  
Drop-in caching middleware. Instead of exact-match, uses vector similarity to return cached answers for semantically equivalent questions. Configurable similarity threshold, TTL, cache warming, analytics. 3-line integration.

```python
from semanticcache import CacheMiddleware
cached_client = CacheMiddleware(anthropic_client, similarity_threshold=0.92)
# Transparent — use exactly like the normal client
```

**Stack:** Python, Redis, Qdrant, FastAPI, Anthropic API  
**Wow factor:** 42% cache hit rate on real query logs = 42% direct cost elimination  

**JD requirements hit:** Context Engineering, Production-grade, AI Governance, LLM APIs  

---

### PHASE 9 — WEEK 10: Specialized Domain Agents
*Domain-specific agents with reflection loops. Interview demo material.*

---

#### PROJECT 22 — BrowserAgent
**Tagline:** Autonomous Web Research Agent with Planning + Reflection  
**Status:** To Build  
**Difficulty:** VERY HIGH | **Days:** 4  

**What it does:**  
Full browser automation agent: plan → search → navigate → extract → reflect → iterate. Playwright for real browser control. Loop detection, citation tracking, structured report generation. Built from primitives, not wrappers.

**Architecture:**
```
Brief → Planner → [Search → Navigate → Extract → Reflect]* → Report
                         ↑_________________________________|
                         (iterate until confidence threshold)
```

**Stack:** Playwright, LangGraph, Anthropic API, FastAPI  
**Wow factor:** Produces sourced competitive analysis from one sentence, fully autonomously  

**JD requirements hit:** Autonomous Agents, LangGraph, Production-grade, Context Engineering  

---

#### PROJECT 23 — SQLAgent Pro
**Tagline:** Text-to-SQL with Self-Correction, Explanation & Safety Layer  
**Status:** To Build  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
NL-to-SQL with full reflection loop: generates SQL → executes → checks plausibility → self-corrects → explains in plain English → enforces read-only safety. Works across PostgreSQL, SQLite, BigQuery.

**Stack:** Python, Anthropic API, SQLAlchemy, FastAPI, React  
**Benchmark:** 89% success rate on Spider benchmark, self-corrects in < 3 attempts  

**JD requirements hit:** Autonomous Agents, Production-grade, AI Guardrails, LLM APIs  

---

#### PROJECT 24 — DebateArena
**Tagline:** Multi-Agent Deliberation System for High-Stakes Decisions  
**Status:** To Build  
**Difficulty:** HIGH | **Days:** 3  

**What it does:**  
Multi-agent framework where specialized agents argue different positions (devil's advocate, optimist, risk analyst, domain expert), then a judge agent synthesizes a structured decision.

**Architecture:**
```
Question/Decision
      ↓
  ┌──────────────────────────────────┐
  │ Devil's Advocate │ Optimist      │
  │ Risk Analyst     │ Domain Expert │
  └──────────────────────────────────┘
      ↓ (structured debate transcript)
  Judge Agent → Final Decision + Reasoning + Confidence
```

**Stack:** LangGraph, Anthropic API, FastAPI, React  
**Wow factor:** Demo: 3-agent debate catches critical flaw that solo LLM missed  

**JD requirements hit:** Autonomous Agents, LangGraph, Context Engineering, Safety Controls  

---

## FOUNDATION PROJECT — Second Brain OS

Ingests GitHub repos, YouTube videos, documentation, RSS feeds → processes with Claude → writes structured notes to Obsidian vault at `/Volumes/VeN/Claude-Code-Work/Brain`

**Why it's the foundation:**
- It feeds research on everything being built (LangGraph, MCP, RAG)
- Demonstrates context engineering, multi-agent pipelines, production error handling
- The vault becomes a live portfolio artifact — 10 weeks of structured AI research
- Phase 2 adds an MCP server → becomes project #25

**Vault location:** `/Volumes/VeN/Claude-Code-Work/Brain`  
**Project location:** `/Volumes/VeN/Claude-Code-Work/projects/second-brain-os`  
**CLI command:** `sbo run`  

---

## PORTFOLIO NARRATIVE ARC

**Act I — "I understand the fundamentals deeply" (Projects 1-5)**  
ContextForge + RAGBench Pro + AgentOrchestra = you know what most candidates skip

**Act II — "I can build complex systems" (Projects 6-12)**  
MCPForge + GraphRAG Engine + PromptOpt = systems thinking

**Act III — "I build for production reality" (Projects 13-19)**  
SelfHeal + GuardStack + EvalEngine + ToolForge = you've thought about what breaks

**Thesis — "I ship systems that work reliably at scale" (Projects 20-24)**  
LiveRAG + SemanticCache + BrowserAgent = the complete picture

---

## JOB REQUIREMENTS COVERAGE MAP

| Requirement (from job postings) | Projects that demonstrate it |
|--------------------------------|------------------------------|
| Context Engineering | 01, 02, 14, 15, 21 |
| RAG Architectures + Vector DBs | 02, 11, 16, 20 |
| LangGraph / Multi-Agent | 03, 05, 18, 22, 24 |
| MCP Protocol | 06, 07 |
| Evaluation Frameworks | 02, 08, 12, 17 |
| AI Guardrails + Safety | 07, 09, 19 |
| PII/PHI Handling | 07, 09 |
| Production-grade systems | All 24 |
| AI Governance + Model Lifecycle | 08, 10, 12, 17 |
| Autonomous Agents | 03, 04, 05, 13, 18, 22, 23 |
| Knowledge Graphs / GraphRAG | 11 |
| Prompt Engineering | 01, 12, 15 |

---

## BENCHMARK STANDARDS

Every project must have `scripts/benchmark.py` that outputs:

```markdown
## Evaluation Results

**Setup:** [dataset], [model], [baseline description]
**Reproduce:** `python scripts/benchmark.py --dataset [name]`

| Metric | Baseline | Ours | Delta |
|--------|----------|------|-------|
| [metric 1] | [value] | [value] | [+/- %] |
| [metric 2] | [value] | [value] | [+/- %] |
| Cost/1k queries | $X.XX | $X.XX | -XX% |
| Latency p95 | Xs | Xs | -XX% |
```

**Approved benchmark datasets:**
- HotpotQA — multi-hop question answering
- MS MARCO — passage ranking and retrieval
- Spider — text-to-SQL
- HumanEval — code generation
- RAGAS built-in — RAG-specific evaluation
- GraphRAG-Bench — graph RAG evaluation

---

## PRIORITY BUILD ORDER

1. **Second Brain OS** (foundation — running during all other builds)
2. **ContextForge** (rarest skill, leads portfolio)
3. **MCPForge Suite** (fastest-growing protocol, PyPI published)
4. **SelfHeal** (most underrepresented, senior signal)
5. **DocIQ** (most domain-specific, directly targets Apple role)
6. **EvalEngine** (critical senior signal — measurement thinking)
7. **AgentOrchestra** (most impressive demo)
8. **RAGBench Pro** (strongest benchmark story)
9. **MCPGuard** (only MCP security framework)
10. **BrowserAgent** (best interview demo)

---

## WHAT CLAUDE CODE MUST KNOW

1. **Always check this document first** — understand which portfolio project this is and what it's meant to demonstrate

2. **Build the benchmark harness before core logic** — `scripts/benchmark.py` exists before the first feature is written

3. **Every project connects to the vault** — if relevant research is found during build, write a note to `Brain/02-Projects/[project-folder]/`

4. **The narrative matters** — code comments should explain the design decision, not just the implementation. Hiring engineers read code.

5. **Cost is a feature** — every project tracks LLM costs. Cost-consciousness is a production signal.

6. **Failure modes are features** — document what breaks and how the system handles it. Graceful degradation is a senior signal.

---

## CURRENT STATUS

| # | Project | Status | GitHub |
|---|---------|--------|--------|
| 0 | Second Brain OS | 🔨 Building | TBD |
| 1 | ContextForge | ⬜ Queued | TBD |
| 2 | RAGBench Pro | ⬜ Queued | TBD |
| 3 | AgentOrchestra | ⬜ Queued | TBD |
| 4 | MemoryOS | ⬜ Queued | TBD |
| 5 | AutoResearch v2 | ⬜ Queued | TBD |
| 6 | MCPForge Suite | ⬜ Queued | TBD |
| 7 | MCPGuard | ⬜ Queued | TBD |
| 8 | EvalEngine | ⬜ Queued | TBD |
| 9 | GuardStack | ⬜ Queued | TBD |
| 10 | LLMScope | ⬜ Queued | TBD |
| 11 | GraphRAG Engine | ⬜ Queued | TBD |
| 12 | PromptOpt | ⬜ Queued | TBD |
| 13 | ToolForge | ⬜ Queued | TBD |
| 14 | StructOut | ⬜ Queued | TBD |
| 15 | SemanticRouter | ⬜ Queued | TBD |
| 16 | DocIQ | ⬜ Queued | TBD |
| 17 | SynthGen | ⬜ Queued | TBD |
| 18 | SelfHeal | ⬜ Queued | TBD |
| 19 | RedTeamKit | ⬜ Queued | TBD |
| 20 | LiveRAG | ⬜ Queued | TBD |
| 21 | SemanticCache | ⬜ Queued | TBD |
| 22 | BrowserAgent | ⬜ Queued | TBD |
| 23 | SQLAgent Pro | ⬜ Queued | TBD |
| 24 | DebateArena | ⬜ Queued | TBD |

---

*Last updated: April 2026*  
*Feed this document to Claude Code at the start of every build session.*  
*Path: /Volumes/VeN/Claude-Code-Work/PORTFOLIO.md*
