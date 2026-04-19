# NL2SQL + Real-Time Visualization Platform — Design Spec
**Date:** 2026-03-24
**Project:** `projects/nl2sql-viz`
**Status:** In Review

---

## 1. Overview

A production-grade SaaS platform that lets users connect their real-time databases and ask natural language questions to get instant, beautiful data visualizations. Built with Python/FastAPI, Claude Agent SDK, BUN sandboxed execution, and Vega-Lite rendering.

**Key differentiators:**
- Real-time data ingestion (live queries + CDC/Kafka streaming + scheduled refresh)
- Agentic loop — Claude autonomously explores schema, writes SQL, transforms data, generates charts
- BUN as a server-side code execution sandbox for complex data transformations
- Universal DB support via plugin interface (PostgreSQL first)

**Target users:** Developers, analysts, startups, businesses (SaaS) → enterprise internal tool later.

---

## 2. Architecture

**Pattern:** Layered Monolith (Phase 1) — architect with clean service interfaces to extract components later.

### Components

```
Frontend (Next.js)
├── Query Input (chat UI)
├── Vega-Lite Chart Renderer (vega-embed)
├── Table / Stats View
├── DB Connection Wizard
├── WebSocket Client (with reconnect logic)
└── Dashboard Builder

Backend (FastAPI/Python)
├── REST API (auth, DB connections, user management)
├── WebSocket Server (streaming results)
├── Scheduler (refresh mode)
├── Async Task Queue (BUN jobs — future extraction point)
├── Connection Manager (encrypted credential store)
└── Session / Schema Cache

Real-time Layer
├── CDC Listener (Debezium)
├── Kafka Consumer
├── Webhook Receiver
└── Cron Scheduler → WebSocket push

Claude Agent SDK — Multi-Agent System
├── Coordinator Agent (orchestrates sub-agents, routing decisions)
├── Schema Agent (DB introspection, schema map, caching)
├── SQL Agent (NL2SQL + retry loop, max 3 iterations)
├── Code Exec Agent (BUN sandbox — complex transformations)
└── Viz Agent (Vega-Lite spec generation, chart type selection)

DB Connector Layer
├── asyncpg (PostgreSQL — Phase 1)
├── Plugin interface (MySQL, SQLite, BigQuery, Snowflake…)
├── Connection modes: Direct / SSH Tunnel / Cloud IAM / Agent Proxy
└── Read-only query enforcement at driver level

BUN Execution Sandbox
├── BUN subprocess inside Docker container (isolated)
├── Linux namespaces + seccomp filter (no FS/network syscalls)
├── Hard timeout (30s) + memory cap (512MB via cgroups)
├── Async task queue wrapper (future: extract to service)
└── Outputs: Vega-Lite JSON, computed tables, statistics
```

---

## 3. Query Lifecycle (Data Flow)

1. **User types query** → browser sends via WebSocket → FastAPI creates session context, dispatches to Coordinator Agent (~50ms)
2. **Coordinator starts agentic loop** → determines intent → calls Schema Agent → streams "Analyzing your database…" to UI (~200ms)
3. **Schema Agent** → reads tables, columns, FK relationships → builds compact schema map → caches for session (TTL: 10min; invalidated by CDC DDL event if CDC is enabled, or by SQL Agent retry failure if CDC is absent) (~300ms)
4. **SQL Agent** → writes SQL → executes → checks result shape → rewrites and retries if wrong (max 3x) → streams SQL to UI for transparency (~500ms–2s)
5. **Code Exec Agent (BUN)** — optional, only when Coordinator routes here (see Section 7) → writes JS/TS script → runs sandboxed → outputs shaped data (~300ms)
6. **Viz Agent** → selects best chart type → generates full Vega-Lite JSON with title, axis labels, colors (~400ms)
7. **WebSocket streams result** → browser renders chart via vega-embed → user sees SQL used, raw data table, can pin to dashboard (~50ms)

**Total latency:** ~1–2s (simple) / ~2–4s (complex with BUN)

---

## 4. Real-Time Modes

| Mode | Trigger | Mechanism |
|---|---|---|
| **Live Query** | User asks a question | Runs on demand against current DB state, no caching |
| **Stream (CDC/Kafka)** | DB row changes | Debezium captures changes → Kafka topic → consumer pushes updated viz via WebSocket to subscribed session |
| **Scheduled Refresh** | Cron timer | Scheduler re-runs SQL Agent for pinned dashboard charts every N seconds/minutes |

**WebSocket lifecycle:**
- Each WebSocket connection is bound to a session ID
- Kafka consumers are registered per-session when stream mode is activated
- On WebSocket disconnect: consumer is paused (not killed) for 60s, then cleaned up if client doesn't reconnect
- Backpressure: updates are debounced at 500ms minimum interval per chart — faster Kafka events are coalesced, not queued
- Schema cache invalidation via CDC: Debezium must be configured with `include.schema.changes=true` to emit DDL events. When a DDL event is received for a connected DB, the Schema Agent cache for that connection is invalidated. If CDC is not enabled for a user's DB, cache invalidation falls back to TTL-only (10min) plus SQL Agent retry failure detection.

---

## 5. Security Model

### Phase 1 — Minimal Auth Gate
Before any DB credential can be stored or queried, a user must authenticate. Phase 1 implementation: API key per user (issued on registration, stored as bcrypt hash).

**REST endpoints:** Require `Authorization: Bearer <api_key>` header on every request.

**WebSocket auth:** Browsers cannot set custom headers on WebSocket upgrades. Auth is handled via a first-message handshake: the client sends `{"type": "auth", "api_key": "<key>"}` as the first WebSocket message. The server validates the key, upgrades the connection to an authenticated session, or closes with code 4001 (unauthorized). All subsequent messages on the connection are scoped to that session. No credential in the store is accessible without a valid session.

### DB Connectivity Methods

| Method | Description | Use Case |
|---|---|---|
| Direct | Encrypted creds (AES-256 at rest), TLS in transit | Internal DBs, dev/staging |
| SSH Tunnel | Bastion host tunnel before DB connection | Private VPCs, production DBs |
| Cloud IAM | AWS RDS IAM / GCP Cloud SQL connectors | Managed cloud databases |
| Agent/Proxy | Lightweight Python agent inside user's network | Air-gapped or strict enterprise |

**Rules across all modes:**
- Credentials never logged, never passed to Claude in query context
- All SQL enforced as read-only at driver level (SET TRANSACTION READ ONLY)
- Connection strings stored AES-256 encrypted, decrypted only at query time in memory

### BUN Sandbox Isolation (Critical)
BUN is not sandboxed by default — explicit OS-level isolation is required:
- BUN subprocess runs inside a minimal Docker container (no network interface, read-only filesystem except `/tmp`)
- Linux seccomp filter blocks all syscalls except those required for JS execution
- cgroups v2 enforces: CPU limit (1 core), memory limit (512MB), wall-clock timeout (30s)
- The BUN process receives only the input data as stdin JSON — no DB credentials, no API keys
- Output is read from stdout as JSON — process is killed and output discarded if it exceeds 30s or 512MB

---

## 6. Error Handling & Failure Modes

| Component | Failure | User sees | System action |
|---|---|---|---|
| SQL Agent (3 retries exhausted) | Cannot generate correct SQL | "I couldn't generate a working query. Here's what I tried: [SQL shown]. Try rephrasing." | Session preserved, user can retry |
| BUN subprocess (timeout) | Code takes >30s | "Data transformation timed out. Try simplifying the analysis." | Process killed, WebSocket kept open |
| BUN subprocess (crash) | Process exits non-zero | "Analysis script failed. Falling back to raw SQL result." | Fallback: return raw SQL data without transformation |
| DB connection drop | asyncpg connection error | "Lost connection to your database. Reconnecting…" | Auto-reconnect with exponential backoff (3 attempts, then error) |
| Kafka consumer lag | Consumer falls behind | Silent — coalesced updates, no notification unless >60s lag | Alert logged, dead-letter queue for missed events, alert Venkat |
| Schema cache stale | ALTER TABLE mid-session | Silent on first query failure → Schema Agent re-fetches | On SQL Agent retry failure, invalidate cache and re-run Schema Agent |
| WebSocket disconnect | Client drops mid-query | — | Query continues server-side; result cached for 60s for reconnect |

---

## 7. Agent Routing Rules (SQL Agent vs. Code Exec Agent)

The **Coordinator Agent** decides which agents to invoke. Routing rule between SQL Agent and Code Exec Agent:

**SQL Agent only** (default path):
- Aggregations expressible in SQL (GROUP BY, SUM, AVG, COUNT, window functions)
- Filters, joins, subqueries
- Any query where the DB engine can produce the final result shape

**Code Exec Agent (BUN) — triggered when:**
- The Coordinator determines the transformation requires imperative logic not expressible in standard SQL
- Examples: multi-step rolling averages, pivot tables, percentile ranking across multiple dimensions, string/regex transformations on result sets, custom chart data shaping
- The SQL Agent's result is returned but Coordinator explicitly routes to Code Exec Agent for post-processing

This routing decision is made once by the Coordinator at the start of the agentic loop based on the user's query intent. The Coordinator does not switch paths mid-loop unless the SQL Agent explicitly signals it cannot express the requirement in SQL.

---

## 8. Project Structure

```
projects/nl2sql-viz/
├── app/
│   ├── main.py                  # FastAPI app, WebSocket, REST routes
│   ├── agents/
│   │   ├── coordinator.py       # Coordinator agent (Claude Agent SDK)
│   │   ├── schema_agent.py      # Schema exploration sub-agent
│   │   ├── sql_agent.py         # NL2SQL + retry loop sub-agent
│   │   ├── code_exec_agent.py   # BUN execution sub-agent
│   │   └── viz_agent.py         # Vega-Lite spec generation sub-agent
│   ├── connectors/
│   │   ├── base.py              # Plugin interface (all DBs implement this)
│   │   ├── postgres.py          # asyncpg implementation
│   │   └── ssh_tunnel.py        # SSH tunnel wrapper
│   ├── execution/
│   │   └── bun_sandbox.py       # BUN subprocess + async task queue
│   ├── realtime/
│   │   ├── cdc_listener.py      # Debezium/CDC consumer
│   │   ├── kafka_consumer.py    # Kafka stream handler
│   │   └── scheduler.py         # Cron-based refresh
│   └── core/
│       ├── auth.py              # API key auth, session tokens
│       ├── session.py           # Session + schema cache (TTL: 10min)
│       └── security.py          # Credential encryption (AES-256)
├── frontend/                    # Next.js app
│   ├── src/app/
│   ├── src/components/
│   │   ├── QueryInput.tsx
│   │   ├── VegaChart.tsx        # vega-embed wrapper
│   │   └── DBConnectWizard.tsx
│   └── src/lib/ws.ts            # WebSocket client (with reconnect)
├── tests/
│   ├── unit/                    # Pure function tests (SQL generation, routing logic)
│   ├── integration/             # Mocked DB + agent behavior tests
│   └── evals/                   # Agent quality evals (NL2SQL accuracy)
├── .env.example
└── pyproject.toml
```

---

## 9. Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Package manager | `uv` |
| Backend framework | FastAPI (async) |
| Agent framework | Claude Agent SDK (Python) |
| LLM | Claude Sonnet (default), Claude Opus for complex schema analysis |
| DB driver (Phase 1) | asyncpg (PostgreSQL) |
| Code execution runtime | BUN (JavaScript/TypeScript) |
| Sandbox isolation | Docker + Linux seccomp + cgroups v2 |
| Visualization spec | Vega-Lite v5 |
| Visualization rendering | vega-embed (browser) |
| Real-time streaming | WebSockets (FastAPI) + Apache Kafka + Debezium CDC |
| Frontend | Next.js (App Router) + Tailwind CSS |
| Credential encryption | AES-256 (`cryptography` library) |
| Auth (Phase 1) | API key per user (bcrypt hashed) |

---

## 10. Testing Strategy

| Layer | What | Method |
|---|---|---|
| Unit | SQL generation helpers, routing logic, credential encryption/decryption, BUN output parsing | pytest, no external dependencies |
| Integration | SQL Agent end-to-end with real PostgreSQL (Docker), BUN sandbox execution, WebSocket streaming | pytest + Docker Compose test environment |
| Agent evals | NL2SQL accuracy — set of 50 canonical queries with known correct SQL and result shapes | Custom eval harness, Claude as judge for semantic correctness |
| Security | BUN sandbox escape attempts (write to FS, open network socket, exec subprocess) | Automated test suite of malicious scripts — all must be blocked |
| End-to-end smoke | Full flow: connect DB → ask question → get chart | Playwright against local stack |

**Mocking policy:** Claude API calls are mocked in unit and integration tests. Real Claude is used only in eval runs to control cost.

---

## 11. Deployment

**Development:** Docker Compose — FastAPI + PostgreSQL + Kafka + Zookeeper + Debezium all local. `docker-compose up` starts the full stack.

**Production (Phase 1 SaaS):**
- FastAPI app: single container, horizontally scalable behind a load balancer
- BUN sandbox: runs as a **sidecar container pool** — the FastAPI container submits BUN jobs to a pool of pre-warmed, isolated BUN containers via a local Unix socket. No Docker-in-Docker (DinD requires privileged mode which defeats sandbox isolation). Each BUN container is ephemeral: spawned per-job, killed on completion. Pool size: 5 containers (configurable). This is the primary extraction point for Phase 2 scaling.
- Kafka: Redpanda Cloud (managed, simpler than self-hosted Confluent)
- Debezium: self-hosted connector pointed at user's DB (or Debezium Cloud)
- Frontend: Vercel (Next.js)
- DB for platform state (users, connections, sessions): PostgreSQL (managed, e.g., Supabase)

---

## 12. Known Technical Debt (Fix Post-Foundation)

1. **BUN scaling** — BUN runs as subprocess inside FastAPI. At high concurrent load, extract BUN execution to its own service. The async task queue wrapper makes this extraction clean when needed.
2. **Async streaming discipline** — All three real-time modes share the FastAPI event loop. Must enforce async/await discipline throughout to prevent blocking. If issues arise, move CDC/Kafka consumers to separate worker processes.

---

## 13. Out of Scope (Phase 1)

- Full OAuth / SSO authentication (Phase 2 — API key is the Phase 1 auth gate)
- MySQL, SQLite, BigQuery connectors (plugin interface ready, implement after Postgres)
- Dashboard persistence (save to DB) — Phase 2
- Collaborative dashboards — Phase 3
- Self-hosted enterprise packaging — post-SaaS

---

## 14. Success Criteria

- User connects a PostgreSQL DB and gets a chart from a natural language question in under 5 seconds p95 **for queries resolved on first SQL attempt** (no retry). Queries requiring SQL Agent retries target ≤10 seconds p95 (up to 3 retries × ~2s each).
- SQL Agent retry loop handles ≥80% of queries correctly without manual intervention (measured via eval harness)
- BUN sandbox blocks all tested escape attempts (filesystem write, network open, subprocess exec)
- All three real-time modes (live, stream, scheduled) work end-to-end on Postgres
- System handles 20 concurrent users without p95 latency exceeding 8 seconds
- Error rate (unhandled exceptions surfaced to user) < 2% of queries
