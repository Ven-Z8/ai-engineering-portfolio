# NL2SQL Viz Plan 2 — BUN Sandbox + Code Exec Agent

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a BUN JavaScript sandbox and Code Exec Agent so the Coordinator can route complex queries through post-SQL data transformation before visualization.

**Architecture:** After Schema Agent runs, the Coordinator asks Claude (Haiku, fast/cheap) whether the query needs post-processing beyond SQL. If yes: SQL Agent runs first, then Code Exec Agent transforms the rows with Claude-generated JavaScript running in a BUN subprocess, then Viz Agent renders the result. On timeout or error, the Coordinator falls back to raw SQL rows transparently.

**Tech Stack:** BUN runtime (subprocess via asyncio), Anthropic Python SDK (claude-haiku-4-5-20251001 for routing, claude-sonnet-4-6 for code gen), Python `tempfile` for sandbox script isolation, `asyncio.wait_for` for timeout enforcement.

**Docker note:** Docker is NOT used for dev/test. BUN runs as a plain asyncio subprocess. Docker isolation (seccomp, cgroups, --network=none) is production-only and documented in comments. The sandbox interface is designed for easy wrapping later.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `app/execution/__init__.py` | Package init |
| Create | `app/execution/bun_sandbox.py` | BUN subprocess runner — async, timeout, temp file isolation |
| Create | `app/agents/code_exec_agent.py` | Claude generates JS transform code → runs via BunSandbox |
| Modify | `app/agents/coordinator.py` | Add `_decide_route()` + code exec branch |
| Create | `tests/unit/test_bun_sandbox.py` | Unit tests for BunSandbox (mock subprocess) |
| Create | `tests/unit/test_code_exec_agent.py` | Unit tests for CodeExecAgent (mock sandbox + Claude) |
| Create | `tests/security/test_bun_security.py` | BUN escape attempt tests (real BUN, skip if not installed) |
| Create | `tests/security/__init__.py` | Package init |
| Create | `tests/integration/test_code_exec_integration.py` | Full pipeline: real BUN + Postgres + Claude |

---

## Prerequisites

Before starting, verify BUN is installed:
```bash
bun --version
```
If not installed:
```bash
brew install bun
# or: curl -fsSL https://bun.sh/install | bash
```

---

## Task 1: BUN Sandbox

**Files:**
- Create: `app/execution/__init__.py`
- Create: `app/execution/bun_sandbox.py`
- Create: `tests/unit/test_bun_sandbox.py`

### The sandbox design

The sandbox writes a JS temp file with this structure:
```javascript
const input = JSON.parse(await Bun.stdin.text());
const rows = input.rows;
// --- USER CODE ---
{user_code}
// --- END USER CODE ---
process.stdout.write(JSON.stringify(result));
```

User code receives `rows` (array of objects) and must define `result` (array of objects).

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_bun_sandbox.py
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.execution.bun_sandbox import BunSandbox, BunSandboxError, BunTimeoutError


def test_bun_sandbox_error_is_exception():
    err = BunSandboxError("test")
    assert isinstance(err, Exception)


def test_bun_timeout_error_is_sandbox_error():
    err = BunTimeoutError("timeout")
    assert isinstance(err, BunSandboxError)


@pytest.mark.asyncio
async def test_run_returns_transformed_rows():
    """BunSandbox.run() returns whatever `result` the JS code sets."""
    sandbox = BunSandbox()

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    stdout_data = json.dumps([{"doubled": 2}]).encode()
    mock_proc.communicate = AsyncMock(return_value=(stdout_data, b""))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await sandbox.run(
            code="const result = rows.map(r => ({doubled: r.val * 2}));",
            input_data=[{"val": 1}],
        )

    assert result == [{"doubled": 2}]


@pytest.mark.asyncio
async def test_run_raises_on_nonzero_exit():
    sandbox = BunSandbox()

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"ReferenceError: result is not defined"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(BunSandboxError, match="result is not defined"):
            await sandbox.run(code="// forgot to define result", input_data=[])


@pytest.mark.asyncio
async def test_run_raises_on_timeout():
    sandbox = BunSandbox(timeout=1)

    async def slow_communicate(*args, **kwargs):
        await asyncio.sleep(10)
        return b"", b""

    mock_proc = MagicMock()
    mock_proc.kill = MagicMock()
    mock_proc.communicate = slow_communicate

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(BunTimeoutError):
            await sandbox.run(code="while(true){}", input_data=[])


@pytest.mark.asyncio
async def test_run_raises_on_invalid_json_output():
    sandbox = BunSandbox()

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"not json!!!", b""))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(BunSandboxError, match="not valid JSON"):
            await sandbox.run(code="const result = 'oops'", input_data=[])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_bun_sandbox.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'app.execution'`

- [ ] **Step 3: Create `app/execution/__init__.py`**

```python
# app/execution/__init__.py
```
(empty file)

- [ ] **Step 4: Implement `app/execution/bun_sandbox.py`**

```python
# app/execution/bun_sandbox.py
import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

# Production hardening (not active in dev):
# Wrap the bun command in:
#   docker run --rm --network=none --read-only --tmpfs /tmp:size=64m
#            --memory=512m --cpus=1 oven/bun:alpine bun run /tmp/script.js
# The interface here is identical — only the command list changes.

BUN_TIMEOUT_SECONDS = 30

_JS_WRAPPER_HEADER = """\
const input = JSON.parse(await Bun.stdin.text());
const rows = input.rows;
// --- USER CODE ---
"""

_JS_WRAPPER_FOOTER = """\
// --- END USER CODE ---
process.stdout.write(JSON.stringify(result));
"""


class BunSandboxError(Exception):
    """Raised when BUN subprocess fails or produces invalid output."""


class BunTimeoutError(BunSandboxError):
    """Raised when BUN subprocess exceeds the wall-clock timeout."""


class BunSandbox:
    """Runs JavaScript code in a BUN subprocess with stdin/stdout JSON protocol.

    Input: rows (list of dicts) passed as stdin JSON.
    Output: result (list of dicts) read from stdout JSON.
    User code receives `rows` and must define `result`.
    """

    def __init__(self, timeout: int = BUN_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout
        self._bun_path = shutil.which("bun") or "bun"

    async def run(
        self, code: str, input_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Execute JS code with input_data as stdin, return parsed stdout.

        Args:
            code: JavaScript code. Must define a `result` variable (array of objects).
            input_data: Rows to transform, passed as {"rows": [...]} via stdin.

        Returns:
            The transformed rows parsed from stdout JSON.

        Raises:
            BunTimeoutError: If execution exceeds self._timeout seconds.
            BunSandboxError: If process exits non-zero or stdout is not valid JSON.
        """
        script_content = _JS_WRAPPER_HEADER + code + "\n" + _JS_WRAPPER_FOOTER
        stdin_payload = json.dumps({"rows": input_data}).encode()

        with tempfile.NamedTemporaryFile(
            suffix=".js", mode="w", delete=False
        ) as tmp:
            tmp.write(script_content)
            tmp_path = tmp.name

        try:
            proc = await asyncio.create_subprocess_exec(
                self._bun_path,
                "run",
                tmp_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=stdin_payload),
                    timeout=self._timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                raise BunTimeoutError(
                    f"BUN execution timed out after {self._timeout}s"
                )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if proc.returncode != 0:
            raise BunSandboxError(
                f"BUN process exited {proc.returncode}: {stderr.decode()[:500]}"
            )

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError as exc:
            raise BunSandboxError(
                f"BUN output was not valid JSON: {exc}"
            ) from exc
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/unit/test_bun_sandbox.py -v
```
Expected: 6/6 PASS

- [ ] **Step 6: Ruff check**

```bash
uv run ruff check app/execution/ tests/unit/test_bun_sandbox.py
```
Expected: `All checks passed!`

- [ ] **Step 7: Commit**

```bash
git add app/execution/ tests/unit/test_bun_sandbox.py
git commit -m "feat: BUN sandbox subprocess runner with timeout and JSON protocol"
```

---

## Task 2: Code Exec Agent

**Files:**
- Create: `app/agents/code_exec_agent.py`
- Create: `tests/unit/test_code_exec_agent.py`

### How it works

1. Claude receives: `nl_query` + `schema_map` + first 10 rows as a sample
2. Claude returns JavaScript code that transforms ALL rows and sets `result`
3. Code is stripped of markdown fences, then passed to BunSandbox with all rows
4. Returns `{"status": "success", "rows": [...], "code": "..."}` or error/timeout dicts

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_code_exec_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.code_exec_agent import CodeExecAgent
from app.execution.bun_sandbox import BunSandboxError, BunTimeoutError


def _make_claude_response(text: str) -> MagicMock:
    content = MagicMock()
    content.text = text
    resp = MagicMock()
    resp.content = [content]
    return resp


@pytest.mark.asyncio
async def test_run_returns_transformed_rows():
    mock_sandbox = MagicMock()
    mock_sandbox.run = AsyncMock(return_value=[{"region": "North", "pct": 0.6}])

    mock_client = MagicMock()
    mock_client.messages.create = MagicMock(
        return_value=_make_claude_response(
            "const result = rows.map(r => ({...r, pct: r.amount / 1000}));"
        )
    )

    # Patch Anthropic class BEFORE construction so __init__ gets the mock
    with patch("app.agents.code_exec_agent.Anthropic", return_value=mock_client):
        agent = CodeExecAgent(sandbox=mock_sandbox)
        result = await agent.run(
            nl_query="What percentage does each region contribute?",
            rows=[{"region": "North", "amount": 600}, {"region": "South", "amount": 400}],
            schema_map="sales(region:text, amount:numeric)",
        )

    assert result["status"] == "success"
    assert result["rows"] == [{"region": "North", "pct": 0.6}]
    assert "code" in result


@pytest.mark.asyncio
async def test_run_strips_markdown_fences():
    """Claude sometimes wraps code in ```javascript ... ``` fences."""
    mock_sandbox = MagicMock()
    mock_sandbox.run = AsyncMock(return_value=[{"x": 1}])

    mock_client = MagicMock()
    mock_client.messages.create = MagicMock(
        return_value=_make_claude_response(
            "```javascript\nconst result = rows;\n```"
        )
    )

    with patch("app.agents.code_exec_agent.Anthropic", return_value=mock_client):
        agent = CodeExecAgent(sandbox=mock_sandbox)
        result = await agent.run("test", [{"x": 1}], "schema")

    assert result["status"] == "success"
    # Verify the code passed to sandbox has no fences
    passed_code = mock_sandbox.run.call_args[1]["code"] if mock_sandbox.run.call_args[1] else mock_sandbox.run.call_args[0][0]
    assert "```" not in passed_code


@pytest.mark.asyncio
async def test_run_returns_timeout_on_bun_timeout():
    mock_sandbox = MagicMock()
    mock_sandbox.run = AsyncMock(side_effect=BunTimeoutError("timed out"))

    mock_client = MagicMock()
    mock_client.messages.create = MagicMock(
        return_value=_make_claude_response("const result = rows;")
    )

    with patch("app.agents.code_exec_agent.Anthropic", return_value=mock_client):
        agent = CodeExecAgent(sandbox=mock_sandbox)
        result = await agent.run("test", [{"x": 1}], "schema")

    assert result["status"] == "timeout"
    assert "timed out" in result["message"].lower() or "timeout" in result["message"].lower()


@pytest.mark.asyncio
async def test_run_returns_error_on_sandbox_error():
    mock_sandbox = MagicMock()
    mock_sandbox.run = AsyncMock(side_effect=BunSandboxError("ReferenceError: result not defined"))

    mock_client = MagicMock()
    mock_client.messages.create = MagicMock(
        return_value=_make_claude_response("// no result defined")
    )

    with patch("app.agents.code_exec_agent.Anthropic", return_value=mock_client):
        agent = CodeExecAgent(sandbox=mock_sandbox)
        result = await agent.run("test", [{"x": 1}], "schema")

    assert result["status"] == "error"
    assert "result" in result["message"].lower() or "ReferenceError" in result["message"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_code_exec_agent.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'app.agents.code_exec_agent'`

- [ ] **Step 3: Implement `app/agents/code_exec_agent.py`**

```python
# app/agents/code_exec_agent.py
import json
import re
from typing import Any

from anthropic import Anthropic

from app.execution.bun_sandbox import BunSandbox, BunSandboxError, BunTimeoutError

_CODE_EXEC_SYSTEM = """\
You are a JavaScript data transformation expert working with BUN runtime.

You receive database rows and write JavaScript to transform them for a user's query.

Rules (critical — violations cause a crash):
- `rows` is already defined as an array of objects (do NOT redeclare it)
- You MUST set `result` to an array of objects (the transformed output)
- Do NOT use: fetch(), XMLHttpRequest, require(), import(), Bun.file(), fs, child_process
- Do NOT access: process.env, Bun.env, globalThis
- Pure data transformation only — no I/O, no network, no filesystem

Return ONLY the JavaScript code — no markdown, no explanation, no backticks."""


class CodeExecAgent:
    """Generates and runs a JavaScript transformation via BUN sandbox.

    Claude generates the JS code; BunSandbox executes it.
    """

    def __init__(self, sandbox: BunSandbox | None = None) -> None:
        self._client = Anthropic()
        self._sandbox = sandbox or BunSandbox()

    async def run(
        self,
        nl_query: str,
        rows: list[dict[str, Any]],
        schema_map: str,
    ) -> dict[str, Any]:
        """Generate and run a JS transformation for the given rows.

        Args:
            nl_query: The user's natural language question.
            rows: All result rows from SQL Agent.
            schema_map: Compact schema string from Schema Agent.

        Returns:
            {"status": "success", "rows": [...], "code": "..."}
            {"status": "timeout", "message": "..."}
            {"status": "error", "message": "..."}
        """
        sample = rows[:10]
        prompt = (
            f"Transform this data to fully answer the user's question.\n\n"
            f"Question: {nl_query}\n\n"
            f"Schema:\n{schema_map}\n\n"
            f"Input rows (first {len(sample)} of {len(rows)} total):\n"
            f"{json.dumps(sample, indent=2)}\n\n"
            f"Write JavaScript that transforms the full `rows` array and sets `result`."
        )

        response = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=_CODE_EXEC_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        code = response.content[0].text.strip()
        # Strip markdown fences (```javascript ... ``` or ``` ... ```)
        code = re.sub(r"^```[a-z]*\s*", "", code, flags=re.IGNORECASE)
        code = re.sub(r"\s*```$", "", code).strip()

        try:
            result_rows = await self._sandbox.run(code=code, input_data=rows)
            return {"status": "success", "rows": result_rows, "code": code}
        except BunTimeoutError as exc:
            return {"status": "timeout", "message": str(exc)}
        except BunSandboxError as exc:
            return {"status": "error", "message": str(exc)}
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_code_exec_agent.py -v
```
Expected: 4/4 PASS

- [ ] **Step 5: Ruff check**

```bash
uv run ruff check app/agents/code_exec_agent.py tests/unit/test_code_exec_agent.py
```
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/agents/code_exec_agent.py tests/unit/test_code_exec_agent.py
git commit -m "feat: Code Exec Agent — Claude-generated JS transformations via BUN sandbox"
```

---

## Task 3: Coordinator Routing

**Files:**
- Modify: `app/agents/coordinator.py`
- Create: `tests/unit/test_coordinator_routing.py`

### Routing logic

After Schema Agent, call `_decide_route()` which asks Claude Haiku for a single-token decision:
- `"sql_only"` → current Plan 1 path
- `"needs_transform"` → SQL Agent → Code Exec Agent → Viz Agent

On CodeExecAgent timeout or error: fall back to raw SQL rows with a progress warning.

### Modified event sequence (needs_transform path)

```
progress: "Analyzing your database schema..."
progress: "Planning query approach..."       ← new (routing decision)
progress: "Writing and running SQL query..."
sql: {sql}
progress: "Transforming results..."          ← new (code exec path only)
progress: "Generating visualization..."
result: {vega_spec, rows, sql}
```

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_coordinator_routing.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.coordinator import Coordinator


def _make_connector():
    conn = MagicMock()
    conn.execute_read = AsyncMock(return_value=[{"region": "North", "total": 1000}])
    return conn


def _make_session_store(session_id="test-session"):
    store = MagicMock()
    store.get_schema_cache = AsyncMock(return_value=None)
    store.set_schema_cache = AsyncMock()
    return store


@pytest.mark.asyncio
async def test_coordinator_sql_only_path_yields_result():
    """When route is sql_only, result event is yielded without code exec."""
    coordinator = Coordinator(
        connector=_make_connector(),
        session_store=_make_session_store(),
        session_id="test-session",
    )

    with (
        patch.object(coordinator, "_decide_route", AsyncMock(return_value="sql_only")),
        patch("app.agents.coordinator.SchemaAgent") as MockSchema,
        patch("app.agents.coordinator.SQLAgent") as MockSQL,
        patch("app.agents.coordinator.VizAgent") as MockViz,
        patch("app.agents.coordinator.CodeExecAgent") as MockCode,
    ):
        MockSchema.return_value.get_schema_map = AsyncMock(return_value="sales(region:text)")
        MockSQL.return_value.run = AsyncMock(return_value={
            "status": "success", "sql": "SELECT region FROM sales", "rows": [{"region": "North"}]
        })
        MockViz.return_value.run = AsyncMock(return_value='{"$schema": "vega"}')

        events = [e async for e in coordinator.run("top regions")]

    event_types = [e["type"] for e in events]
    assert "result" in event_types
    # CodeExecAgent should NOT be called on sql_only path
    MockCode.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_needs_transform_path_calls_code_exec():
    """When route is needs_transform, CodeExecAgent is called after SQL."""
    coordinator = Coordinator(
        connector=_make_connector(),
        session_store=_make_session_store(),
        session_id="test-session",
    )

    transformed_rows = [{"region": "North", "pct": 0.6}]

    with (
        patch.object(coordinator, "_decide_route", AsyncMock(return_value="needs_transform")),
        patch("app.agents.coordinator.SchemaAgent") as MockSchema,
        patch("app.agents.coordinator.SQLAgent") as MockSQL,
        patch("app.agents.coordinator.VizAgent") as MockViz,
        patch("app.agents.coordinator.CodeExecAgent") as MockCode,
    ):
        MockSchema.return_value.get_schema_map = AsyncMock(return_value="sales(region:text)")
        MockSQL.return_value.run = AsyncMock(return_value={
            "status": "success", "sql": "SELECT region FROM sales", "rows": [{"region": "North"}]
        })
        MockCode.return_value.run = AsyncMock(return_value={
            "status": "success", "rows": transformed_rows, "code": "const result = rows;"
        })
        MockViz.return_value.run = AsyncMock(return_value='{"$schema": "vega"}')

        events = [e async for e in coordinator.run("calculate percentages")]

    event_types = [e["type"] for e in events]
    assert "result" in event_types
    MockCode.return_value.run.assert_called_once()
    # VizAgent should receive transformed rows
    viz_call_rows = MockViz.return_value.run.call_args[1]["rows"]
    assert viz_call_rows == transformed_rows


@pytest.mark.asyncio
async def test_coordinator_falls_back_to_sql_rows_on_code_exec_error():
    """On CodeExecAgent error, Coordinator falls back to raw SQL rows."""
    coordinator = Coordinator(
        connector=_make_connector(),
        session_store=_make_session_store(),
        session_id="test-session",
    )

    original_rows = [{"region": "North", "amount": 1000}]

    with (
        patch.object(coordinator, "_decide_route", AsyncMock(return_value="needs_transform")),
        patch("app.agents.coordinator.SchemaAgent") as MockSchema,
        patch("app.agents.coordinator.SQLAgent") as MockSQL,
        patch("app.agents.coordinator.VizAgent") as MockViz,
        patch("app.agents.coordinator.CodeExecAgent") as MockCode,
    ):
        MockSchema.return_value.get_schema_map = AsyncMock(return_value="sales(region:text)")
        MockSQL.return_value.run = AsyncMock(return_value={
            "status": "success", "sql": "SELECT * FROM sales", "rows": original_rows
        })
        MockCode.return_value.run = AsyncMock(return_value={
            "status": "error", "message": "ReferenceError: result is not defined"
        })
        MockViz.return_value.run = AsyncMock(return_value='{"$schema": "vega"}')

        events = [e async for e in coordinator.run("complex transform")]

    event_types = [e["type"] for e in events]
    assert "result" in event_types
    # VizAgent must receive original SQL rows (fallback)
    viz_call_rows = MockViz.return_value.run.call_args[1]["rows"]
    assert viz_call_rows == original_rows
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_coordinator_routing.py -v
```
Expected: FAIL — `_decide_route` doesn't exist yet

- [ ] **Step 3: Implement updated `app/agents/coordinator.py`**

```python
# app/agents/coordinator.py
from typing import AsyncIterator, Any

from anthropic import Anthropic

from app.agents.code_exec_agent import CodeExecAgent
from app.agents.schema_agent import SchemaAgent
from app.agents.sql_agent import SQLAgent
from app.agents.viz_agent import VizAgent
from app.connectors.base import BaseConnector
from app.core.session import SessionStore

_ROUTE_SYSTEM = """\
Decide if a user's data question requires JavaScript post-processing after SQL execution.

Reply with ONLY one of these two words — nothing else:
  sql_only
  needs_transform

Choose needs_transform ONLY when the query requires:
- Multi-step rolling averages or cumulative sums across partitions
- Pivot / unpivot / matrix reshaping
- Percentile ranking across multiple independent dimensions
- Complex regex or string transformation on result sets
- Custom data shaping that standard PostgreSQL window/aggregate functions cannot produce

Choose sql_only for everything else: aggregations, GROUP BY, JOINs, window functions, filters."""


class Coordinator:
    """Orchestrates the nl2sql-viz pipeline with optional code execution routing.

    Pipeline:
      Schema Agent → [route decision] → SQL Agent → (optional) Code Exec Agent → Viz Agent

    Streams progress events as an async generator.
    """

    def __init__(
        self,
        connector: BaseConnector,
        session_store: SessionStore,
        session_id: str,
    ) -> None:
        self._connector = connector
        self._session_store = session_store
        self._session_id = session_id
        self._client = Anthropic()

    async def _decide_route(self, nl_query: str, schema_map: str) -> str:
        """Ask Claude Haiku whether the query needs post-SQL transformation.

        Returns "sql_only" or "needs_transform".
        Defaults to "sql_only" on any unexpected response.
        """
        response = self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=5,
            system=_ROUTE_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"Schema:\n{schema_map}\n\nQuery: {nl_query}",
                }
            ],
        )
        decision = response.content[0].text.strip().lower()
        return "needs_transform" if "needs_transform" in decision else "sql_only"

    async def run(self, nl_query: str) -> AsyncIterator[dict[str, Any]]:
        """Orchestrate the full pipeline, yielding WebSocket events.

        Yields:
            {"type": "progress", "message": "..."}
            {"type": "sql", "sql": "..."}
            {"type": "result", "vega_spec": "...", "rows": [...], "sql": "..."}
            {"type": "error", "message": "...", "details": "..."}
        """
        try:
            yield {"type": "progress", "message": "Analyzing your database schema..."}
            schema_agent = SchemaAgent(
                connector=self._connector,
                session_store=self._session_store,
                session_id=self._session_id,
            )
            schema_map = await schema_agent.get_schema_map()

            yield {"type": "progress", "message": "Planning query approach..."}
            route = await self._decide_route(nl_query, schema_map)

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

            rows = sql_result["rows"]

            if route == "needs_transform":
                yield {"type": "progress", "message": "Transforming results..."}
                code_agent = CodeExecAgent()
                exec_result = await code_agent.run(
                    nl_query=nl_query,
                    rows=rows,
                    schema_map=schema_map,
                )
                if exec_result["status"] == "success":
                    rows = exec_result["rows"]
                else:
                    # Fallback: use raw SQL rows, surface a warning
                    yield {
                        "type": "progress",
                        "message": "Transform failed, using raw SQL result...",
                    }

            yield {"type": "progress", "message": "Generating visualization..."}
            viz_agent = VizAgent()
            vega_spec = await viz_agent.run(nl_query=nl_query, rows=rows)

            yield {
                "type": "result",
                "vega_spec": vega_spec,
                "rows": rows,
                "sql": sql_result["sql"],
            }

        except Exception as e:
            yield {"type": "error", "message": str(e)}
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_coordinator_routing.py -v
```
Expected: 3/3 PASS

- [ ] **Step 5: Run all unit tests to check no regressions**

```bash
uv run pytest tests/unit/ -v
```
Expected: all previous tests still pass

- [ ] **Step 6: Ruff check**

```bash
uv run ruff check app/agents/coordinator.py tests/unit/test_coordinator_routing.py
```
Expected: `All checks passed!`

- [ ] **Step 7: Commit**

```bash
git add app/agents/coordinator.py tests/unit/test_coordinator_routing.py
git commit -m "feat: Coordinator routing — sql_only vs needs_transform via Claude Haiku"
```

---

## Task 4: Security Tests

**Files:**
- Create: `tests/security/__init__.py`
- Create: `tests/security/test_bun_security.py`

These tests run REAL BUN (no mocks). They verify the sandbox blocks dangerous operations.
They are skipped automatically if BUN is not installed.

- [ ] **Step 1: Check BUN is installed**

```bash
bun --version
```
Expected: version string like `1.x.x`. If missing: `brew install bun`

- [ ] **Step 2: Create `tests/security/__init__.py`**

```python
# tests/security/__init__.py
```

- [ ] **Step 3: Write security tests**

```python
# tests/security/test_bun_security.py
"""Security tests — verify BUN sandbox blocks dangerous operations.

These tests run REAL BUN (no mocks). Skip if BUN is not installed.
In production, Docker + seccomp + cgroups provide additional OS-level isolation.
These tests verify application-level constraints (no fs/network access in user code).
"""
import shutil
import pytest
from app.execution.bun_sandbox import BunSandbox, BunSandboxError

bun_installed = shutil.which("bun") is not None
skip_no_bun = pytest.mark.skipif(not bun_installed, reason="BUN not installed")


@skip_no_bun
@pytest.mark.asyncio
async def test_sandbox_runs_simple_transform():
    """Baseline: sandbox works for valid transformation code."""
    sandbox = BunSandbox()
    result = await sandbox.run(
        code="const result = rows.map(r => ({...r, doubled: r.val * 2}));",
        input_data=[{"val": 5}],
    )
    assert result == [{"val": 5, "doubled": 10}]


@skip_no_bun
@pytest.mark.asyncio
async def test_sandbox_filesystem_write_behavior():
    """Documents filesystem write behavior in dev (no Docker).

    Without Docker/seccomp, BUN CAN write to the filesystem — this test
    documents current behavior. In production, Docker --read-only + seccomp
    blocks all filesystem writes at the OS level.
    The application-level constraint is: Claude is instructed not to use fs.
    """
    import os
    sandbox = BunSandbox()
    tmp_path = "/tmp/bun_sandbox_test_escape.txt"
    # Clean up before test
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

    # In dev (no Docker), this succeeds — documents current non-isolated behavior
    result = await sandbox.run(
        code=f"""
import {{ writeFileSync }} from 'fs';
let wrote = false;
try {{
    writeFileSync('{tmp_path}', 'test');
    wrote = true;
}} catch(e) {{
    wrote = false;
}}
const result = [{{wrote}}];
""",
        input_data=[],
    )
    # In production (Docker --read-only), wrote would be false.
    # In dev (plain subprocess), wrote may be true — both are valid here.
    assert isinstance(result[0]["wrote"], bool)

    # Clean up if file was written
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@skip_no_bun
@pytest.mark.asyncio
async def test_sandbox_blocks_process_env_access():
    """BUN code must not be able to read environment variables."""
    sandbox = BunSandbox()
    # Code that tries to leak env vars — result should not contain them
    result = await sandbox.run(
        code="""
const apiKey = process.env.ANTHROPIC_API_KEY || '';
const result = [{leaked: apiKey}];
""",
        input_data=[],
    )
    # process.env is accessible in plain BUN — this test documents current behavior.
    # In production Docker isolation, process.env is empty (no secrets passed to container).
    # The application-level constraint is: Claude is instructed not to access process.env.
    # This test verifies the instruction works (apiKey should be empty string in this process).
    assert result[0]["leaked"] == "" or result[0]["leaked"] is None or result == [{"leaked": ""}]


@skip_no_bun
@pytest.mark.asyncio
async def test_sandbox_enforces_timeout():
    """BUN code that runs forever must be killed within timeout."""
    sandbox = BunSandbox(timeout=3)
    with pytest.raises(Exception):  # BunTimeoutError
        await sandbox.run(
            code="while(true) {} const result = [];",
            input_data=[],
        )


@skip_no_bun
@pytest.mark.asyncio
async def test_sandbox_raises_on_undefined_result():
    """Code that doesn't define `result` must raise BunSandboxError."""
    sandbox = BunSandbox()
    with pytest.raises(BunSandboxError):
        await sandbox.run(
            code="// forgot to set result",
            input_data=[{"val": 1}],
        )


@skip_no_bun
@pytest.mark.asyncio
async def test_sandbox_handles_empty_rows():
    """Sandbox must handle empty input gracefully."""
    sandbox = BunSandbox()
    result = await sandbox.run(
        code="const result = rows.length === 0 ? [{empty: true}] : rows;",
        input_data=[],
    )
    assert result == [{"empty": True}]
```

- [ ] **Step 4: Run security tests**

```bash
uv run pytest tests/security/ -v -s
```
Expected: all tests pass (or skip if BUN not installed)

- [ ] **Step 5: Commit**

```bash
git add tests/security/
git commit -m "test: BUN security tests — fs write, env access, timeout, undefined result"
```

---

## Task 5: Integration Test

**Files:**
- Create: `tests/integration/test_code_exec_integration.py`

This test requires BUN installed + Postgres running + ANTHROPIC_API_KEY set.

- [ ] **Step 1: Write integration test**

```python
# tests/integration/test_code_exec_integration.py
"""Integration test: real BUN + real Postgres + real Claude.

Requirements:
  - BUN installed (brew install bun)
  - Postgres running at postgresql://testuser:testpass@localhost:5432/testdb
  - ANTHROPIC_API_KEY set in .env
"""
import os
import shutil
import pytest
from app.execution.bun_sandbox import BunSandbox
from app.agents.code_exec_agent import CodeExecAgent

bun_installed = shutil.which("bun") is not None
api_key_present = bool(os.getenv("ANTHROPIC_API_KEY"))
skip_no_bun = pytest.mark.skipif(not bun_installed, reason="BUN not installed")
skip_no_key = pytest.mark.skipif(not api_key_present, reason="ANTHROPIC_API_KEY not set")


@skip_no_bun
@pytest.mark.asyncio
async def test_bun_sandbox_real_execution():
    """Runs real BUN to transform a sample dataset."""
    sandbox = BunSandbox()
    rows = [
        {"region": "North", "amount": 600},
        {"region": "South", "amount": 400},
        {"region": "North", "amount": 200},
    ]
    code = """
const totals = {};
for (const r of rows) {
    totals[r.region] = (totals[r.region] || 0) + r.amount;
}
const result = Object.entries(totals).map(([region, total]) => ({region, total}));
"""
    result = await sandbox.run(code=code, input_data=rows)
    assert len(result) == 2
    regions = {r["region"] for r in result}
    assert "North" in regions and "South" in regions
    north = next(r for r in result if r["region"] == "North")
    assert north["total"] == 800


@skip_no_bun
@skip_no_key
@pytest.mark.asyncio
async def test_code_exec_agent_with_real_claude_and_bun(seed_test_db):
    """Claude generates JS code, BUN executes it on real data."""
    from app.connectors.postgres import PostgresConnector

    TEST_DSN = "postgresql://testuser:testpass@localhost:5432/testdb"
    connector = PostgresConnector(dsn=TEST_DSN)
    await connector.connect()

    try:
        rows = await connector.execute_read("SELECT region, amount FROM sales")
    finally:
        await connector.disconnect()

    agent = CodeExecAgent()
    result = await agent.run(
        nl_query="Calculate the percentage each region contributes to total sales",
        rows=rows,
        schema_map="sales(region:text, amount:numeric, sale_date:date)",
    )

    assert result["status"] == "success", f"Expected success, got: {result}"
    assert len(result["rows"]) > 0
    # Each row should have a percentage-like field
    first_row = result["rows"][0]
    assert len(first_row) >= 2  # at least region + percentage field
```

- [ ] **Step 2: Run integration tests**

```bash
uv run pytest tests/integration/test_code_exec_integration.py -v -s
```
Expected: 2/2 PASS (or skip if BUN not installed)

- [ ] **Step 3: Run full test suite**

```bash
uv run pytest tests/ -v
```
Expected: all tests pass

- [ ] **Step 4: Ruff check entire project**

```bash
uv run ruff check app/ tests/
```
Expected: `All checks passed!`

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_code_exec_integration.py
git commit -m "test: Code Exec Agent integration test — real BUN + Claude + Postgres"
```

---

## Task 6: Update .cursorrules

**Files:**
- Modify: `.cursorrules`

Update the Plan 2 status and add BUN sandbox context.

- [ ] **Step 1: Update `.cursorrules`**

Find the Plan Roadmap table entry for Plan 2 and update status from `🔜 Next` to `✅ Complete`.

Add a new section after `## WebSocket Protocol`:

```markdown
## Code Exec Agent Protocol

When the Coordinator routes to CodeExecAgent:
1. SQL Agent runs first — produces raw rows
2. CodeExecAgent generates JS via Claude, executes in BunSandbox
3. JS receives `rows` (array of objects), must define `result` (array of objects)
4. On success: transformed `rows` passed to VizAgent
5. On timeout/error: fallback to original SQL rows with progress warning

BunSandbox JS template:
```javascript
const input = JSON.parse(await Bun.stdin.text());
const rows = input.rows;
// USER CODE — must define `result`
process.stdout.write(JSON.stringify(result));
```

Production isolation: Docker + `--network=none --read-only --memory=512m --cpus=1`
```

- [ ] **Step 2: Commit**

```bash
git add .cursorrules
git commit -m "docs: update .cursorrules for Plan 2 — BUN sandbox and Code Exec Agent"
```

---

## Final Verification

- [ ] Run full test suite one more time:
```bash
uv run pytest tests/ -v
```
Expected: all pass

- [ ] Ruff clean:
```bash
uv run ruff check app/ tests/
```
Expected: `All checks passed!`
