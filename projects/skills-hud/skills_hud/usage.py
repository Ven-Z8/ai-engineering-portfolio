"""Parse Claude Code session logs to count Skill tool invocations.

Session logs live at `~/.claude/projects/**/*.jsonl`. Each assistant turn that
calls the `Skill` tool appears as a JSON line containing a `tool_use` content
block named `Skill` whose `input.skill` is the requested skill key.

We do a fast string-prefilter (`"name":"Skill"`) before parsing each line as
JSON, because a single session file can be megabytes long and most lines do
not reference the Skill tool.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


@dataclass
class UsageStats:
    counts: dict[str, int]           # raw skill string -> total count
    counts_30d: dict[str, int]       # within last 30 days
    last_used: dict[str, datetime]   # most recent invocation per skill string
    sessions_scanned: int            # number of session files read


def parse_usage(projects_dir: Path | None = None, now: datetime | None = None) -> UsageStats:
    """Walk every session JSONL and count Skill tool calls."""
    projects_dir = projects_dir or (Path.home() / ".claude" / "projects")
    counts: dict[str, int] = defaultdict(int)
    counts_30d: dict[str, int] = defaultdict(int)
    last_used: dict[str, datetime] = {}
    sessions = 0
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    if not projects_dir.exists():
        return UsageStats({}, {}, {}, 0)

    for jsonl in _iter_session_files(projects_dir):
        sessions += 1
        try:
            with jsonl.open(encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if '"name":"Skill"' not in line:
                        continue
                    skill, ts = _extract_skill_call(line)
                    if not skill:
                        continue
                    counts[skill] += 1
                    if ts:
                        if ts >= cutoff:
                            counts_30d[skill] += 1
                        prev = last_used.get(skill)
                        if prev is None or ts > prev:
                            last_used[skill] = ts
        except OSError:
            continue

    return UsageStats(dict(counts), dict(counts_30d), last_used, sessions)


def _iter_session_files(projects_dir: Path) -> Iterator[Path]:
    yield from projects_dir.rglob("*.jsonl")


def _extract_skill_call(line: str) -> tuple[str | None, datetime | None]:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None, None
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return None, None
    content = msg.get("content")
    if not isinstance(content, list):
        return None, None
    ts = _parse_ts(obj.get("timestamp"))
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "tool_use" or block.get("name") != "Skill":
            continue
        skill = (block.get("input") or {}).get("skill")
        if isinstance(skill, str) and skill.strip():
            return skill.strip(), ts
    return None, None


def _parse_ts(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
