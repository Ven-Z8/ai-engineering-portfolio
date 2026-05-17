"""Parse Claude Code session logs and count skill invocations from three signal sources.

Each JSONL line in `~/.claude/projects/**/*.jsonl` is scanned for:

  tool : an explicit `Skill` tool-use block in an assistant message
  cmd  : a `<command-name>/<value>` tag (slash-command marker emitted by the harness)
  auto : a system-reminder phrase like `your 'plugin:name' skill` (SessionStart auto-load)

If multiple sources reference the same skill on a single line, we keep only the
highest-priority one (tool > cmd > auto) so a single user action is counted once,
not three times. Per-source counts are tracked separately so the UI can show that
e.g. `using-superpowers` is loaded by hooks rather than chosen.

Skill strings that don't match any installed skill (e.g. built-in CLI commands
like `/plugin`, `/status`, `/login`) stay in the counters but the API layer
reports them as `unmatched_calls` rather than attributing them to any skill row.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

SOURCES = ("tool", "cmd", "auto")
_PRIORITY = {"tool": 3, "cmd": 2, "auto": 1}

_CMD_RE = re.compile(r"<command-name>/([^<\s]+)</command-name>")
_AUTOLOAD_RE = re.compile(r"your '([a-z][a-z0-9:_.\-]+)' skill")


@dataclass
class UsageStats:
    by_source: dict[str, dict[str, int]] = field(default_factory=dict)       # skill -> {source: count}
    by_source_30d: dict[str, dict[str, int]] = field(default_factory=dict)
    last_used: dict[str, datetime] = field(default_factory=dict)
    sessions_scanned: int = 0

    def total(self, skill: str) -> int:
        return sum(self.by_source.get(skill, {}).values())

    def total_30d(self, skill: str) -> int:
        return sum(self.by_source_30d.get(skill, {}).values())


def parse_usage(projects_dir: Path | None = None, now: datetime | None = None) -> UsageStats:
    projects_dir = projects_dir or (Path.home() / ".claude" / "projects")
    by_source: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_source_30d: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    last_used: dict[str, datetime] = {}
    sessions = 0
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    if not projects_dir.exists():
        return UsageStats()

    for jsonl in _iter_session_files(projects_dir):
        sessions += 1
        try:
            with jsonl.open(encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    ts, signals = _extract_signals(line)
                    if not signals:
                        continue
                    for skill, source in signals.items():
                        by_source[skill][source] += 1
                        if ts and ts >= cutoff:
                            by_source_30d[skill][source] += 1
                        if ts:
                            prev = last_used.get(skill)
                            if prev is None or ts > prev:
                                last_used[skill] = ts
        except OSError:
            continue

    return UsageStats(
        by_source={k: dict(v) for k, v in by_source.items()},
        by_source_30d={k: dict(v) for k, v in by_source_30d.items()},
        last_used=last_used,
        sessions_scanned=sessions,
    )


def _iter_session_files(projects_dir: Path) -> Iterator[Path]:
    yield from projects_dir.rglob("*.jsonl")


def _extract_signals(line: str) -> tuple[datetime | None, dict[str, str]]:
    """Return (timestamp, {skill_string: source}) with priority dedupe per line."""
    has_tool = '"name":"Skill"' in line
    has_cmd = "<command-name>/" in line
    has_auto = "' skill" in line and "your '" in line
    if not (has_tool or has_cmd or has_auto):
        return None, {}

    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None, {}
    ts = _parse_ts(obj.get("timestamp"))

    found: dict[str, str] = {}

    def _record(skill: str, source: str) -> None:
        skill = skill.strip()
        if not skill:
            return
        existing = found.get(skill)
        if existing is None or _PRIORITY[source] > _PRIORITY[existing]:
            found[skill] = source

    if has_tool:
        msg = obj.get("message")
        if isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use" or block.get("name") != "Skill":
                        continue
                    skill = (block.get("input") or {}).get("skill")
                    if isinstance(skill, str):
                        _record(skill, "tool")

    if has_cmd:
        for m in _CMD_RE.finditer(line):
            _record(m.group(1), "cmd")

    if has_auto:
        for m in _AUTOLOAD_RE.finditer(line):
            _record(m.group(1), "auto")

    return ts, found


def _parse_ts(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
