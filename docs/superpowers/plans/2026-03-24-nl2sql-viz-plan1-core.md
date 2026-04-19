# NL2SQL Viz — Plan 1: Core Agent Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the working core: user connects a PostgreSQL database, asks a natural language question, and gets a rendered Vega-Lite chart back via WebSocket in under 5 seconds.

**Architecture:** FastAPI backend with Claude Agent SDK multi-agent system (Coordinator → Schema Agent → SQL Agent → Viz Agent). WebSocket streams progress and results to a minimal Next.js frontend. Authentication via API key with first-message WebSocket handshake.

**Tech Stack:** Python 3.12, uv, FastAPI, asyncpg, Claude Agent SDK (Python), Vega-Lite v5, Next.js 14 (App Router), Tailwind CSS, vega-embed, pytest, Docker Compose (dev)

**Spec:** `docs/superpowers/specs/2026-03-24-nl2sql-viz-design.md`

**Out of scope for this plan:** BUN/Code Exec Agent, CDC/Kafka, scheduled refresh, dashboard builder, SSH tunnel, Cloud IAM connectors.

---

## File Map

```
projects/nl2sql-viz/
├── pyproject.toml                        # uv project, dependencies
├── .env.example                          # ANTHROPIC_API_KEY, DATABASE_URL
├── docker-compose.yml                    # FastAPI + Postgres for dev
├── app/
│   ├── main.py                           # FastAPI app, routes, WebSocket endpoint
│   ├── core/
│   │   ├── auth.py                       # API key hashing, validation, session model
│   │   ├── security.py                   # AES-256 credential encryption/decryption
│   │   └── session.py                    # Session store, schema cache (TTL: 10min)
│   ├── connectors/
│   │   ├── base.py                       # Abstract connector interface
│   │   └── postgres.py                   # asyncpg implementation
│   └── agents/
│       ├── coordinator.py                # Coordinator agent — orchestrates sub-agents
│       ├── schema_agent.py               # Schema introspection sub-agent + tools
│       ├── sql_agent.py                  # NL2SQL sub-agent + retry loop + tools
│       └── viz_agent.py                  # Vega-Lite spec generation sub-agent
├── tests/
│   ├── unit/
│   │   ├── test_auth.py                  # API key hash, validate
│   │   ├── test_security.py              # AES-256 encrypt/decrypt round-trip
│   │   ├── test_session.py               # Session create, schema cache TTL
│   │   └── test_viz_agent.py             # Vega-Lite spec shape validation
│   └── integration/
│       ├── conftest.py                   # Docker Postgres fixture, test API key
│       ├── test_postgres_connector.py    # Connect, execute read-only query
│       ├── test_schema_agent.py          # Schema Agent against real Postgres
│       ├── test_sql_agent.py             # SQL Agent end-to-end with real Postgres
│       └── test_websocket.py             # WebSocket auth handshake + query flow
└── frontend/
    ├── package.json
    ├── src/
    │   ├── app/
    │   │   └── page.tsx                  # Single page: query input + chart output
    │   ├── components/
    │   │   ├── QueryInput.tsx            # Text input + submit button
    │   │   └── VegaChart.tsx             # vega-embed wrapper component
    │   └── lib/
    │       └── ws.ts                     # WebSocket client with auth handshake + reconnect
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `projects/nl2sql-viz/pyproject.toml`
- Create: `projects/nl2sql-viz/.env.example`
- Create: `projects/nl2sql-viz/docker-compose.yml`

- [ ] **Step 1: Initialize uv project**

```bash
cd /Volumes/VeN/Claude-Code-Work/projects/nl2sql-viz
uv init --no-readme
uv add fastapi uvicorn[standard] asyncpg cryptography passlib[bcrypt] python-dotenv claude-agent-sdk anthropic
uv add --dev pytest pytest-asyncio httpx
```

- [ ] **Step 2: Verify installed packages**

```bash
uv run python -c "import fastapi, asyncpg, cryptography, passlib, anthropic; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Create .env.example**

```bash
# .env.example
ANTHROPIC_API_KEY=your_anthropic_api_key_here
SECRET_KEY=32_byte_hex_string_for_aes256_here
```

- [ ] **Step 4: Create docker-compose.yml for dev Postgres**

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
      POSTGRES_DB: testdb
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser"]
      interval: 5s
      timeout: 5s
      retries: 5
```

- [ ] **Step 5: Start Postgres and verify it's up**

```bash
docker compose up -d
docker compose ps
```
Expected: postgres service `healthy`

- [ ] **Step 6: Commit**

```bash
git init
git add pyproject.toml .env.example docker-compose.yml
git commit -m "feat: bootstrap nl2sql-viz project with uv and dev postgres"
```

---

## Task 2: Auth Layer

**Files:**
- Create: `app/core/auth.py`
- Create: `tests/unit/test_auth.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_auth.py
import pytest
from app.core.auth import hash_api_key, verify_api_key, generate_api_key

def test_generate_api_key_is_32_chars():
    key = generate_api_key()
    assert len(key) == 32
    assert key.isalnum()

def test_hash_and_verify_roundtrip():
    key = generate_api_key()
    hashed = hash_api_key(key)
    assert verify_api_key(key, hashed) is True

def test_wrong_key_fails_verification():
    key = generate_api_key()
    hashed = hash_api_key(key)
    assert verify_api_key("wrongkey", hashed) is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_auth.py -v
```
Expected: 3 failures — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Implement auth.py**

```python
# app/core/auth.py
import secrets
import string
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_api_key() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(32))

def hash_api_key(api_key: str) -> str:
    return _pwd_context.hash(api_key)

def verify_api_key(api_key: str, hashed: str) -> bool:
    return _pwd_context.verify(api_key, hashed)
```

Also create `app/__init__.py` and `app/core/__init__.py` (empty).

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/test_auth.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/auth.py app/__init__.py app/core/__init__.py tests/unit/test_auth.py
git commit -m "feat: API key generation, hashing, and verification"
```

---

## Task 3: Credential Encryption

**Files:**
- Create: `app/core/security.py`
- Create: `tests/unit/test_security.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_security.py
import pytest
from app.core.security import encrypt_credential, decrypt_credential

SECRET_KEY = "a" * 32  # 32-byte test key

def test_encrypt_decrypt_roundtrip():
    plaintext = "postgresql://user:pass@localhost/db"
    ciphertext = encrypt_credential(plaintext, SECRET_KEY)
    assert ciphertext != plaintext
    assert decrypt_credential(ciphertext, SECRET_KEY) == plaintext

def test_different_encryptions_of_same_value_differ():
    plaintext = "secret"
    c1 = encrypt_credential(plaintext, SECRET_KEY)
    c2 = encrypt_credential(plaintext, SECRET_KEY)
    assert c1 != c2  # random IV per encryption

def test_wrong_key_raises():
    ciphertext = encrypt_credential("secret", SECRET_KEY)
    wrong_key = "b" * 32
    with pytest.raises(Exception):
        decrypt_credential(ciphertext, wrong_key)
```

- [ ] **Step 2: Run to verify failures**

```bash
uv run pytest tests/unit/test_security.py -v
```
Expected: 3 failures

- [ ] **Step 3: Implement security.py**

```python
# app/core/security.py
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_credential(plaintext: str, secret_key: str) -> str:
    key = secret_key.encode()[:32].ljust(32, b"\0")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()

def decrypt_credential(token: str, secret_key: str) -> str:
    key = secret_key.encode()[:32].ljust(32, b"\0")
    aesgcm = AESGCM(key)
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_security.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/security.py tests/unit/test_security.py
git commit -m "feat: AES-256-GCM credential encryption/decryption"
```

---

## Task 4: Session Store + Schema Cache

**Files:**
- Create: `app/core/session.py`
- Create: `tests/unit/test_session.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_session.py
import asyncio
import pytest
from app.core.session import SessionStore

@pytest.mark.asyncio
async def test_create_and_get_session():
    store = SessionStore()
    session_id = await store.create_session(user_id="user1", connection_id="conn1")
    session = await store.get_session(session_id)
    assert session is not None
    assert session["user_id"] == "user1"

@pytest.mark.asyncio
async def test_set_and_get_schema_cache():
    store = SessionStore()
    session_id = await store.create_session(user_id="u1", connection_id="c1")
    schema = {"tables": ["orders", "users"]}
    await store.set_schema_cache(session_id, schema)
    cached = await store.get_schema_cache(session_id)
    assert cached == schema

@pytest.mark.asyncio
async def test_schema_cache_returns_none_after_invalidation():
    store = SessionStore()
    session_id = await store.create_session(user_id="u1", connection_id="c1")
    await store.set_schema_cache(session_id, {"tables": []})
    await store.invalidate_schema_cache(session_id)
    assert await store.get_schema_cache(session_id) is None
```

- [ ] **Step 2: Run to verify failures**

```bash
uv run pytest tests/unit/test_session.py -v
```
Expected: 3 failures

- [ ] **Step 3: Implement session.py**

```python
# app/core/session.py
import time
import uuid
from typing import Any, Optional

SCHEMA_CACHE_TTL_SECONDS = 600  # 10 minutes

class SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._schema_cache: dict[str, dict] = {}  # session_id -> {schema, expires_at}

    async def create_session(self, user_id: str, connection_id: str) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "user_id": user_id,
            "connection_id": connection_id,
            "created_at": time.time(),
        }
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)

    async def set_schema_cache(self, session_id: str, schema: Any) -> None:
        self._schema_cache[session_id] = {
            "schema": schema,
            "expires_at": time.time() + SCHEMA_CACHE_TTL_SECONDS,
        }

    async def get_schema_cache(self, session_id: str) -> Optional[Any]:
        entry = self._schema_cache.get(session_id)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            del self._schema_cache[session_id]
            return None
        return entry["schema"]

    async def invalidate_schema_cache(self, session_id: str) -> None:
        self._schema_cache.pop(session_id, None)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_session.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/core/session.py tests/unit/test_session.py
git commit -m "feat: session store with schema cache (TTL 10min)"
```

---

## Task 5: PostgreSQL Connector

**Files:**
- Create: `app/connectors/base.py`
- Create: `app/connectors/postgres.py`
- Create: `app/connectors/__init__.py`
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_postgres_connector.py`

- [ ] **Step 1: Write connector interface**

```python
# app/connectors/base.py
from abc import ABC, abstractmethod
from typing import Any

class BaseConnector(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def execute_read(self, sql: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_schema(self) -> dict[str, Any]: ...
```

- [ ] **Step 2: Write failing integration tests**

```python
# tests/integration/conftest.py
import pytest

TEST_DSN = "postgresql://testuser:testpass@localhost:5432/testdb"

@pytest.fixture
def postgres_dsn():
    return TEST_DSN
```

```python
# tests/integration/test_postgres_connector.py
import pytest
from app.connectors.postgres import PostgresConnector

@pytest.mark.asyncio
async def test_connect_and_disconnect(postgres_dsn):
    conn = PostgresConnector(dsn=postgres_dsn)
    await conn.connect()
    await conn.disconnect()

@pytest.mark.asyncio
async def test_execute_read_returns_rows(postgres_dsn):
    conn = PostgresConnector(dsn=postgres_dsn)
    await conn.connect()
    rows = await conn.execute_read("SELECT 1 AS num")
    await conn.disconnect()
    assert rows == [{"num": 1}]

@pytest.mark.asyncio
async def test_write_query_is_rejected(postgres_dsn):
    conn = PostgresConnector(dsn=postgres_dsn)
    await conn.connect()
    with pytest.raises(Exception, match="read-only"):
        await conn.execute_read("INSERT INTO pg_class VALUES (1)")
    await conn.disconnect()

@pytest.mark.asyncio
async def test_get_schema_returns_tables(postgres_dsn):
    conn = PostgresConnector(dsn=postgres_dsn)
    await conn.connect()
    schema = await conn.get_schema()
    await conn.disconnect()
    assert "tables" in schema
    assert isinstance(schema["tables"], list)
```

- [ ] **Step 3: Run to verify failures**

```bash
uv run pytest tests/integration/test_postgres_connector.py -v
```
Expected: failures (PostgresConnector not implemented)

- [ ] **Step 4: Implement postgres.py**

```python
# app/connectors/postgres.py
import asyncpg
from typing import Any
from .base import BaseConnector

class PostgresConnector(BaseConnector):
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._conn: asyncpg.Connection | None = None

    async def connect(self) -> None:
        self._conn = await asyncpg.connect(self._dsn)

    async def disconnect(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def execute_read(self, sql: str) -> list[dict[str, Any]]:
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            raise ValueError("read-only queries only (SELECT or WITH)")
        rows = await self._conn.fetch(sql)
        return [dict(row) for row in rows]

    async def get_schema(self) -> dict[str, Any]:
        rows = await self._conn.fetch("""
            SELECT
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                tc.constraint_type
            FROM information_schema.tables t
            JOIN information_schema.columns c
                ON t.table_name = c.table_name AND t.table_schema = c.table_schema
            LEFT JOIN information_schema.key_column_usage kcu
                ON c.column_name = kcu.column_name AND c.table_name = kcu.table_name
            LEFT JOIN information_schema.table_constraints tc
                ON kcu.constraint_name = tc.constraint_name
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name, c.ordinal_position
        """)
        tables: dict[str, list] = {}
        for row in rows:
            tname = row["table_name"]
            if tname not in tables:
                tables[tname] = []
            tables[tname].append({
                "column": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "constraint": row["constraint_type"],
            })
        return {"tables": list(tables.keys()), "columns": tables}
```

- [ ] **Step 5: Run integration tests (Postgres must be running)**

```bash
docker compose up -d
uv run pytest tests/integration/test_postgres_connector.py -v
```
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add app/connectors/ tests/integration/
git commit -m "feat: PostgreSQL connector with read-only enforcement and schema introspection"
```

---

## Task 6: Schema Agent

**Files:**
- Create: `app/agents/schema_agent.py`
- Create: `app/agents/__init__.py`
- Create: `tests/integration/test_schema_agent.py`

- [ ] **Step 1: Write failing integration test**

```python
# tests/integration/test_schema_agent.py
import pytest
from app.agents.schema_agent import SchemaAgent
from app.connectors.postgres import PostgresConnector

@pytest.mark.asyncio
async def test_schema_agent_returns_compact_map(postgres_dsn):
    connector = PostgresConnector(dsn=postgres_dsn)
    await connector.connect()
    agent = SchemaAgent(connector=connector)
    schema_map = await agent.get_schema_map()
    await connector.disconnect()
    assert isinstance(schema_map, str)
    assert len(schema_map) > 10  # non-empty compact representation

@pytest.mark.asyncio
async def test_schema_agent_uses_cache(postgres_dsn, mocker):
    from app.core.session import SessionStore
    store = SessionStore()
    session_id = await store.create_session("u1", "c1")
    connector = PostgresConnector(dsn=postgres_dsn)
    await connector.connect()
    agent = SchemaAgent(connector=connector, session_store=store, session_id=session_id)

    # First call hits DB
    map1 = await agent.get_schema_map()
    # Second call should use cache (connector is closed)
    await connector.disconnect()
    map2 = await agent.get_schema_map()
    assert map1 == map2
```

- [ ] **Step 2: Run to verify failures**

```bash
uv run pytest tests/integration/test_schema_agent.py -v
```
Expected: failures

- [ ] **Step 3: Implement schema_agent.py**

```python
# app/agents/schema_agent.py
import json
from typing import Optional
from app.connectors.base import BaseConnector
from app.core.session import SessionStore

class SchemaAgent:
    """
    Introspects the DB and returns a compact schema map string
    suitable for inclusion in Claude prompts.
    Caches per session — invalidated by TTL or explicit call.
    """
    def __init__(
        self,
        connector: BaseConnector,
        session_store: Optional[SessionStore] = None,
        session_id: Optional[str] = None,
    ):
        self._connector = connector
        self._session_store = session_store
        self._session_id = session_id

    async def get_schema_map(self) -> str:
        # Check cache first
        if self._session_store and self._session_id:
            cached = await self._session_store.get_schema_cache(self._session_id)
            if cached:
                return cached

        schema = await self._connector.get_schema()
        compact = self._build_compact_map(schema)

        if self._session_store and self._session_id:
            await self._session_store.set_schema_cache(self._session_id, compact)

        return compact

    def _build_compact_map(self, schema: dict) -> str:
        lines = []
        for table in schema["tables"]:
            cols = schema["columns"].get(table, [])
            col_strs = []
            for col in cols:
                constraint = f" [{col['constraint']}]" if col["constraint"] else ""
                col_strs.append(f"{col['column']}:{col['type']}{constraint}")
            lines.append(f"{table}({', '.join(col_strs)})")
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/integration/test_schema_agent.py -v
```
Expected: 2 passed. (The mocker test may need `pytest-mock`: run `uv add --dev pytest-mock` if needed.)

- [ ] **Step 5: Commit**

```bash
git add app/agents/ tests/integration/test_schema_agent.py
git commit -m "feat: Schema Agent with compact schema map and session caching"
```

---

## Task 7: SQL Agent

**Files:**
- Create: `app/agents/sql_agent.py`
- Create: `tests/integration/test_sql_agent.py`

The SQL Agent takes a natural language query + schema map, generates SQL via Claude, executes it, and retries up to 3 times if it fails.

- [ ] **Step 1: Seed test data in Postgres**

Add to `tests/integration/conftest.py`:

```python
import asyncpg
import pytest_asyncio

@pytest_asyncio.fixture  # not autouse — only tests that need seeded data should request it
async def seed_test_db():
    conn = await asyncpg.connect("postgresql://testuser:testpass@localhost:5432/testdb")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            region TEXT NOT NULL,
            amount NUMERIC(10,2) NOT NULL,
            sale_date DATE NOT NULL
        )
    """)
    await conn.execute("DELETE FROM sales")
    await conn.execute("""
        INSERT INTO sales (region, amount, sale_date) VALUES
        ('North', 1000.00, '2024-01-15'),
        ('South', 2000.00, '2024-01-20'),
        ('North', 1500.00, '2024-02-10'),
        ('East',  800.00,  '2024-02-15')
    """)
    await conn.close()
```

- [ ] **Step 2: Write failing tests**

```python
# tests/integration/test_sql_agent.py
import pytest
from app.agents.sql_agent import SQLAgent
from app.connectors.postgres import PostgresConnector

SCHEMA_MAP = "sales(id:integer [PRIMARY KEY], region:text, amount:numeric, sale_date:date)"

@pytest.mark.asyncio
async def test_sql_agent_executes_simple_query(postgres_dsn):
    connector = PostgresConnector(dsn=postgres_dsn)
    await connector.connect()
    agent = SQLAgent(connector=connector)
    result = await agent.run(
        nl_query="What is the total sales amount per region?",
        schema_map=SCHEMA_MAP,
    )
    await connector.disconnect()
    assert result["status"] == "success"
    assert isinstance(result["rows"], list)
    assert len(result["rows"]) > 0
    assert "sql" in result

@pytest.mark.asyncio
async def test_sql_agent_returns_error_after_max_retries(postgres_dsn):
    connector = PostgresConnector(dsn=postgres_dsn)
    await connector.connect()
    agent = SQLAgent(connector=connector, max_retries=1)
    result = await agent.run(
        nl_query="gibberish xyzzy frob nitz",
        schema_map=SCHEMA_MAP,
    )
    await connector.disconnect()
    # Either success (Claude infers something) or structured error
    assert result["status"] in ("success", "error")
    if result["status"] == "error":
        assert "attempts" in result
```

- [ ] **Step 3: Run to verify failures**

```bash
uv run pytest tests/integration/test_sql_agent.py -v
```
Expected: failures

- [ ] **Step 4: Implement sql_agent.py**

```python
# app/agents/sql_agent.py
# NOTE: Uses Anthropic SDK directly for Plan 1 simplicity.
# Will be refactored to Claude Agent SDK in a later plan when subagent orchestration is needed.
import os
import re
from typing import Any
from anthropic import Anthropic
from app.connectors.base import BaseConnector

_client = Anthropic()

SQL_SYSTEM_PROMPT = """You are a SQL expert. Given a natural language query and a database schema,
write a single valid PostgreSQL SELECT query that answers the question.
Return ONLY the SQL query — no explanation, no markdown, no backticks.
The query must be a SELECT or WITH statement."""

class SQLAgent:
    def __init__(self, connector: BaseConnector, max_retries: int = 3):
        self._connector = connector
        self._max_retries = max_retries

    async def run(self, nl_query: str, schema_map: str) -> dict[str, Any]:
        messages = []
        last_error = None

        for attempt in range(1, self._max_retries + 1):
            # Build prompt
            user_msg = f"Schema:\n{schema_map}\n\nQuestion: {nl_query}"
            if last_error:
                user_msg += f"\n\nPrevious SQL failed with: {last_error}\nWrite a corrected query."

            messages.append({"role": "user", "content": user_msg})

            response = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SQL_SYSTEM_PROMPT,
                messages=messages,
            )
            sql = response.content[0].text.strip()
            sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
            sql = re.sub(r"```$", "", sql).strip()

            messages.append({"role": "assistant", "content": sql})

            try:
                rows = await self._connector.execute_read(sql)
                return {"status": "success", "sql": sql, "rows": rows, "attempts": attempt}
            except Exception as e:
                last_error = str(e)

        return {
            "status": "error",
            "message": f"Could not generate a working query after {self._max_retries} attempts.",
            "last_error": last_error,
            "attempts": self._max_retries,
        }
```

- [ ] **Step 5: Set ANTHROPIC_API_KEY and run tests**

```bash
export ANTHROPIC_API_KEY=<your_key>
uv run pytest tests/integration/test_sql_agent.py -v
```
Expected: 2 passed (uses real Claude API — costs a few cents)

- [ ] **Step 6: Commit**

```bash
git add app/agents/sql_agent.py tests/integration/test_sql_agent.py tests/integration/conftest.py
git commit -m "feat: SQL Agent with NL2SQL via Claude and 3-attempt retry loop"
```

---

## Task 8: Viz Agent

**Files:**
- Create: `app/agents/viz_agent.py`
- Create: `tests/unit/test_viz_agent.py`

The Viz Agent takes query results (rows) + the original NL query and generates a Vega-Lite v5 JSON spec.

- [ ] **Step 1: Write failing unit tests**

```python
# tests/unit/test_viz_agent.py
import pytest
import json
from unittest.mock import patch, MagicMock
from app.agents.viz_agent import VizAgent

SAMPLE_ROWS = [
    {"region": "North", "total": 2500.00},
    {"region": "South", "total": 2000.00},
    {"region": "East",  "total": 800.00},
]

MOCK_VEGA_SPEC = json.dumps({
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "mark": "bar",
    "data": {"values": SAMPLE_ROWS},
    "encoding": {
        "x": {"field": "region", "type": "nominal"},
        "y": {"field": "total", "type": "quantitative"}
    }
})

def test_viz_agent_returns_valid_vega_spec():
    agent = VizAgent()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=MOCK_VEGA_SPEC)]

    with patch("app.agents.viz_agent._client.messages.create", return_value=mock_response):
        import asyncio
        spec = asyncio.run(agent.run(
            nl_query="Total sales by region",
            rows=SAMPLE_ROWS,
        ))

    parsed = json.loads(spec)
    assert "$schema" in parsed
    assert "mark" in parsed
    assert "data" in parsed
    assert "encoding" in parsed

def test_viz_agent_raises_on_invalid_json():
    agent = VizAgent()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="not valid json {{{")]

    with patch("app.agents.viz_agent._client.messages.create", return_value=mock_response):
        import asyncio
        with pytest.raises(ValueError, match="Invalid Vega-Lite JSON"):
            asyncio.run(agent.run(nl_query="test", rows=[]))
```

- [ ] **Step 2: Run to verify failures**

```bash
uv run pytest tests/unit/test_viz_agent.py -v
```
Expected: failures

- [ ] **Step 3: Implement viz_agent.py**

```python
# app/agents/viz_agent.py
import json
import re
from typing import Any
from anthropic import Anthropic

_client = Anthropic()

VIZ_SYSTEM_PROMPT = """You are a data visualization expert. Given query results and the original question,
generate a valid Vega-Lite v5 JSON specification.

Rules:
- Return ONLY the JSON object — no explanation, no markdown, no backticks
- Use "$schema": "https://vega.github.io/schema/vega-lite/v5.json"
- Embed the data inline in "data": {"values": [...]}
- Choose the most appropriate mark type (bar, line, point, arc) for the data shape
- Add a descriptive title derived from the question
- Use proper axis labels"""

class VizAgent:
    async def run(self, nl_query: str, rows: list[dict[str, Any]]) -> str:
        user_msg = f"Question: {nl_query}\n\nData:\n{json.dumps(rows, indent=2)}"

        response = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=VIZ_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"```$", "", raw).strip()

        try:
            json.loads(raw)  # validate
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid Vega-Lite JSON from Viz Agent: {e}") from e

        return raw
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_viz_agent.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/agents/viz_agent.py tests/unit/test_viz_agent.py
git commit -m "feat: Viz Agent generates Vega-Lite v5 spec from query results"
```

---

## Task 9: Coordinator Agent

**Files:**
- Create: `app/agents/coordinator.py`

The Coordinator orchestrates Schema → SQL → Viz in sequence, streaming progress events.

- [ ] **Step 1: Implement coordinator.py**

No test at this layer — covered by WebSocket integration test in Task 11.

```python
# app/agents/coordinator.py
from typing import AsyncIterator, Any
from app.agents.schema_agent import SchemaAgent
from app.agents.sql_agent import SQLAgent
from app.agents.viz_agent import VizAgent
from app.connectors.base import BaseConnector
from app.core.session import SessionStore

class Coordinator:
    def __init__(
        self,
        connector: BaseConnector,
        session_store: SessionStore,
        session_id: str,
    ):
        self._connector = connector
        self._session_store = session_store
        self._session_id = session_id

    async def run(self, nl_query: str) -> AsyncIterator[dict[str, Any]]:
        """
        Yields progress events and final result as dicts.
        Event shapes:
          {"type": "progress", "message": "..."}
          {"type": "sql", "sql": "..."}
          {"type": "result", "vega_spec": "...", "rows": [...], "sql": "..."}
          {"type": "error", "message": "..."}
        """
        try:
            yield {"type": "progress", "message": "Analyzing your database schema..."}
            schema_agent = SchemaAgent(
                connector=self._connector,
                session_store=self._session_store,
                session_id=self._session_id,
            )
            schema_map = await schema_agent.get_schema_map()

            yield {"type": "progress", "message": "Writing and running SQL query..."}
            sql_agent = SQLAgent(connector=self._connector)
            sql_result = await sql_agent.run(nl_query=nl_query, schema_map=schema_map)

            if sql_result["status"] == "error":
                yield {
                    "type": "error",
                    "message": sql_result["message"],
                    "details": sql_result.get("last_error"),
                }
                return

            yield {"type": "sql", "sql": sql_result["sql"]}
            yield {"type": "progress", "message": "Generating visualization..."}

            viz_agent = VizAgent()
            vega_spec = await viz_agent.run(
                nl_query=nl_query,
                rows=sql_result["rows"],
            )

            yield {
                "type": "result",
                "vega_spec": vega_spec,
                "rows": sql_result["rows"],
                "sql": sql_result["sql"],
            }

        except Exception as e:
            yield {"type": "error", "message": str(e)}
```

- [ ] **Step 2: Commit**

```bash
git add app/agents/coordinator.py
git commit -m "feat: Coordinator Agent orchestrates Schema→SQL→Viz pipeline with progress streaming"
```

---

## Task 10: FastAPI App + WebSocket Endpoint

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: Implement main.py**

```python
# app/main.py
import json
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.auth import generate_api_key, hash_api_key, verify_api_key
from app.core.session import SessionStore
from app.connectors.postgres import PostgresConnector
from app.agents.coordinator import Coordinator

load_dotenv()

session_store = SessionStore()
# In-memory user store for Phase 1 — replace with DB in Phase 2
_users: dict[str, str] = {}  # user_id -> hashed_api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REST: Register user, get API key ---
class RegisterRequest(BaseModel):
    username: str

@app.post("/api/register")
async def register(req: RegisterRequest):
    api_key = generate_api_key()
    _users[req.username] = hash_api_key(api_key)
    return {"api_key": api_key, "username": req.username}

# --- REST: Connect a database ---
class ConnectRequest(BaseModel):
    api_key: str
    dsn: str  # Phase 1: plain DSN. Phase 2: encrypted via security.py

@app.post("/api/connections")
async def connect_db(req: ConnectRequest):
    user_id = _verify_api_key_or_raise(req.api_key)
    # Test the connection
    conn = PostgresConnector(dsn=req.dsn)
    try:
        await conn.connect()
        await conn.disconnect()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot connect to DB: {e}")
    import hashlib
    connection_id = hashlib.sha256(req.dsn.encode()).hexdigest()[:16]  # deterministic
    return {"connection_id": connection_id, "dsn": req.dsn}

def _verify_api_key_or_raise(api_key: str) -> str:
    for user_id, hashed in _users.items():
        if verify_api_key(api_key, hashed):
            return user_id
    raise HTTPException(status_code=401, detail="Invalid API key")

# --- WebSocket: NL query endpoint ---
@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    await websocket.accept()

    # Step 1: Auth handshake (first message must be auth)
    try:
        auth_msg = await websocket.receive_json()
        if auth_msg.get("type") != "auth" or not auth_msg.get("api_key"):
            await websocket.close(code=4001)
            return
        user_id = None
        for uid, hashed in _users.items():
            if verify_api_key(auth_msg["api_key"], hashed):
                user_id = uid
                break
        if not user_id:
            await websocket.close(code=4001)
            return

        await websocket.send_json({"type": "authenticated", "user_id": user_id})

        # Step 2: Handle queries
        while True:
            data = await websocket.receive_json()
            if data.get("type") != "query":
                continue

            nl_query = data.get("query", "").strip()
            dsn = data.get("dsn", "")
            if not nl_query or not dsn:
                await websocket.send_json({"type": "error", "message": "query and dsn required"})
                continue

            session_id = await session_store.create_session(
                user_id=user_id, connection_id=dsn[:16]
            )
            connector = PostgresConnector(dsn=dsn)
            await connector.connect()

            try:
                coordinator = Coordinator(
                    connector=connector,
                    session_store=session_store,
                    session_id=session_id,
                )
                async for event in coordinator.run(nl_query):
                    await websocket.send_json(event)
            finally:
                await connector.disconnect()

    except WebSocketDisconnect:
        pass
```

- [ ] **Step 2: Run the server manually and verify it starts**

```bash
uv run uvicorn app.main:app --reload --port 8000
```
Expected: `Uvicorn running on http://127.0.0.1:8000`

Stop with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: FastAPI app with register, connect, and WebSocket query endpoints"
```

---

## Task 11: WebSocket Integration Test

**Files:**
- Create: `tests/integration/test_websocket.py`

- [ ] **Step 1: Write WebSocket end-to-end test**

```python
# tests/integration/test_websocket.py
import pytest
import json
from httpx import AsyncClient, ASGITransport
from app.main import app

TEST_DSN = "postgresql://testuser:testpass@localhost:5432/testdb"

@pytest.mark.asyncio
async def test_register_and_query_via_websocket():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        resp = await client.post("/api/register", json={"username": "testuser"})
        assert resp.status_code == 200
        api_key = resp.json()["api_key"]

        # WebSocket query
        from starlette.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

    client = TestClient(app)
    with client.websocket_connect("/ws/query") as ws:
        # Auth handshake
        ws.send_json({"type": "auth", "api_key": api_key})
        auth_resp = ws.receive_json()
        assert auth_resp["type"] == "authenticated"

        # Send query
        ws.send_json({
            "type": "query",
            "query": "What is the total sales amount per region?",
            "dsn": TEST_DSN,
        })

        events = []
        for _ in range(20):  # collect up to 20 events
            try:
                event = ws.receive_json(timeout=30)
                events.append(event)
                if event["type"] in ("result", "error"):
                    break
            except Exception:
                break

    event_types = [e["type"] for e in events]
    assert "result" in event_types, f"Expected result event, got: {event_types}"
    result = next(e for e in events if e["type"] == "result")
    assert "vega_spec" in result
    assert "sql" in result

    spec = json.loads(result["vega_spec"])
    assert "$schema" in spec

@pytest.mark.asyncio
async def test_websocket_rejects_bad_api_key():
    client = TestClient(app)
    with client.websocket_connect("/ws/query") as ws:
        ws.send_json({"type": "auth", "api_key": "badkey"})
        # Server should close with 4001
        import pytest
        try:
            ws.receive_json()
            assert False, "Expected disconnect"
        except Exception:
            pass
```

- [ ] **Step 2: Run integration tests**

```bash
export ANTHROPIC_API_KEY=<your_key>
docker compose up -d
uv run pytest tests/integration/test_websocket.py -v
```
Expected: 2 passed

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_websocket.py
git commit -m "test: WebSocket integration test — auth handshake + full NL2SQL query flow"
```

---

## Task 12: Frontend — Minimal Query UI

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/QueryInput.tsx`
- Create: `frontend/src/components/VegaChart.tsx`
- Create: `frontend/src/lib/ws.ts`

- [ ] **Step 1: Initialize Next.js app**

```bash
cd projects/nl2sql-viz/frontend
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"
# When prompted: use src/ dir? No. Use App Router? Yes.
npm install vega vega-lite vega-embed
```

- [ ] **Step 2: Create WebSocket client**

```typescript
// frontend/src/lib/ws.ts
type EventHandler = (event: Record<string, unknown>) => void;

export class QueryWebSocket {
  private ws: WebSocket | null = null;
  private apiKey: string;
  private onEvent: EventHandler;

  constructor(apiKey: string, onEvent: EventHandler) {
    this.apiKey = apiKey;
    this.onEvent = onEvent;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket("ws://localhost:8000/ws/query");

      this.ws.onopen = () => {
        this.ws!.send(JSON.stringify({ type: "auth", api_key: this.apiKey }));
      };

      this.ws.onmessage = (e) => {
        const event = JSON.parse(e.data);
        if (event.type === "authenticated") {
          resolve();
        } else {
          this.onEvent(event);
        }
      };

      this.ws.onerror = reject;
    });
  }

  sendQuery(query: string, dsn: string): void {
    this.ws?.send(JSON.stringify({ type: "query", query, dsn }));
  }

  disconnect(): void {
    this.ws?.close();
  }
}
```

- [ ] **Step 3: Create VegaChart component**

```tsx
// frontend/src/components/VegaChart.tsx
"use client";
import { useEffect, useRef } from "react";
import embed from "vega-embed";

interface VegaChartProps {
  spec: string;
}

export default function VegaChart({ spec }: VegaChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !spec) return;
    embed(containerRef.current, JSON.parse(spec), { actions: false }).catch(console.error);
  }, [spec]);

  return <div ref={containerRef} className="w-full" />;
}
```

- [ ] **Step 4: Create QueryInput component**

```tsx
// frontend/src/components/QueryInput.tsx
"use client";
import { useState } from "react";

interface QueryInputProps {
  onSubmit: (query: string) => void;
  disabled: boolean;
}

export default function QueryInput({ onSubmit, disabled }: QueryInputProps) {
  const [value, setValue] = useState("");
  return (
    <form
      onSubmit={(e) => { e.preventDefault(); if (value.trim()) onSubmit(value); }}
      className="flex gap-2"
    >
      <input
        className="flex-1 border rounded px-3 py-2 text-sm"
        placeholder="Ask a question about your data..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="bg-indigo-600 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
      >
        Ask
      </button>
    </form>
  );
}
```

- [ ] **Step 5: Create main page**

```tsx
// frontend/src/app/page.tsx
"use client";
import { useState, useEffect, useRef } from "react";
import { QueryWebSocket } from "@/lib/ws";
import QueryInput from "@/components/QueryInput";
import VegaChart from "@/components/VegaChart";

const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";
const DSN = process.env.NEXT_PUBLIC_DSN ?? "";

export default function Home() {
  const [status, setStatus] = useState<string>("Connecting...");
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [vegaSpec, setVegaSpec] = useState<string | null>(null);
  const wsRef = useRef<QueryWebSocket | null>(null);

  useEffect(() => {
    const ws = new QueryWebSocket(API_KEY, (event) => {
      setEvents((prev) => [...prev, event]);
      if (event.type === "progress") setStatus(event.message as string);
      if (event.type === "result") {
        setVegaSpec(event.vega_spec as string);
        setLoading(false);
        setStatus("Done");
      }
      if (event.type === "error") {
        setStatus(`Error: ${event.message}`);
        setLoading(false);
      }
    });
    ws.connect().then(() => setStatus("Connected — ask a question"));
    wsRef.current = ws;
    return () => ws.disconnect();
  }, []);

  const handleQuery = (query: string) => {
    setLoading(true);
    setVegaSpec(null);
    setEvents([]);
    wsRef.current?.sendQuery(query, DSN);
  };

  return (
    <main className="max-w-3xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-2">DataLens AI</h1>
      <p className="text-gray-500 text-sm mb-6">{status}</p>
      <QueryInput onSubmit={handleQuery} disabled={loading} />
      {vegaSpec && (
        <div className="mt-8">
          <VegaChart spec={vegaSpec} />
        </div>
      )}
    </main>
  );
}
```

- [ ] **Step 6: Add .env.local.example to frontend**

```bash
# frontend/.env.local.example
NEXT_PUBLIC_API_KEY=your_api_key_here
NEXT_PUBLIC_DSN=postgresql://user:pass@localhost:5432/mydb
```

- [ ] **Step 7: Verify frontend builds without errors**

```bash
cd frontend
npm run build
```
Expected: Build completes with no TypeScript or lint errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: minimal Next.js frontend with WebSocket query client and Vega-Lite chart rendering"
```

---

## Task 13: Run Full Stack Smoke Test

- [ ] **Step 1: Start backend**

```bash
cd projects/nl2sql-viz
export ANTHROPIC_API_KEY=<your_key>
uv run uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Register a user and get an API key**

```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "venkat"}'
```
Expected: `{"api_key": "...", "username": "venkat"}`

- [ ] **Step 3: Start frontend with your API key and DSN**

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_KEY and NEXT_PUBLIC_DSN
npm run dev
```

- [ ] **Step 4: Open browser at http://localhost:3000**
- Type: *"What is the total sales amount per region?"*
- Expected: progress messages appear ("Analyzing schema...", "Writing SQL..."), then a bar chart renders.

- [ ] **Step 5: Run full test suite**

```bash
cd projects/nl2sql-viz
uv run pytest tests/ -v --ignore=tests/integration/test_websocket.py
```
Expected: all unit tests pass without API key. Run with `ANTHROPIC_API_KEY` set for integration tests.

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "feat: Plan 1 complete — NL2SQL core agent loop working end-to-end"
```

---

## What's Next (Plan 2)

Once this plan is complete and working:
- **Plan 2:** BUN sandbox + Code Exec Agent (Docker container pool, seccomp isolation, complex transformations)
- **Plan 3:** Real-time layer (CDC/Debezium, Kafka consumer, scheduled refresh)
- **Plan 4:** Frontend polish (dashboard builder, DB connection wizard, saved queries)
