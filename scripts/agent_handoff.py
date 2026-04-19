#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
HANDOFF_DIR = ROOT / "docs" / "agent-handoff"
TASKS_DIR = HANDOFF_DIR / "tasks"
ACTIVE_TASKS = HANDOFF_DIR / "ACTIVE_TASKS.md"


@dataclass
class TaskRow:
    title: str
    owner: str
    status: str
    updated: str
    next_action: str
    task_file: str

    def to_markdown(self) -> str:
        return (
            f"| {escape_cell(self.title)} | {escape_cell(self.owner)} | {escape_cell(self.status)} | "
            f"{escape_cell(self.updated)} | {escape_cell(self.next_action)} | {escape_cell(self.task_file)} |"
        )


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").strip()


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise SystemExit("Slug cannot be empty.")
    return slug


def ensure_dirs() -> None:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


def task_path(slug: str) -> Path:
    return TASKS_DIR / f"{slug}.md"


def render_list(items: Iterable[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return ", ".join(cleaned) if cleaned else "None"


def read_text(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_meta_line(text: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^- {re.escape(label)}: .*?$", re.MULTILINE)
    replacement = f"- {label}: {value}"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text


def update_active_tasks(slug: str, row: TaskRow) -> None:
    if not ACTIVE_TASKS.exists():
        ACTIVE_TASKS.write_text(
            "# Active Tasks\n\n| Task | Owner | Status | Last Updated | Next Action | File |\n"
            "| --- | --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )

    lines = ACTIVE_TASKS.read_text(encoding="utf-8").splitlines()
    target_file = f"docs/agent-handoff/tasks/{slug}.md"
    new_line = row.to_markdown()
    replaced = False
    output: list[str] = []

    for line in lines:
        if line.startswith("| ") and target_file in line:
            output.append(new_line)
            replaced = True
        elif line.startswith("| _No tracked tasks yet_"):
            if not replaced:
                output.append(new_line)
                replaced = True
        else:
            output.append(line)

    if not replaced:
        if output and output[-1].startswith("| ---"):
            output.append(new_line)
        else:
            output.append(new_line)

    ACTIVE_TASKS.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def create_task(args: argparse.Namespace) -> None:
    ensure_dirs()
    slug = slugify(args.slug or args.title)
    path = task_path(slug)
    if path.exists():
        raise SystemExit(f"Task already exists: {path}")

    updated = now_utc()
    text = f"""# {args.title}\n\n- Task: `{slug}`\n- Current Owner: `{args.owner}`\n- Status: `{args.status}`\n- Last Updated: `{updated}`\n- Next Action: `{args.next}`\n\n## Objective\n\n{args.objective}\n\n## Current State\n\n{args.current_state}\n\n## Working Agreements\n\n- Keep important decisions here.\n- Leave a handoff entry before stopping.\n- Prefer exact next steps over vague summaries.\n\n## Important Files\n\n- Add files that matter for this task.\n\n## Risks / Blockers\n\n- None yet.\n\n## Session Handoffs\n"""
    write_text(path, text)

    update_active_tasks(
        slug,
        TaskRow(
            title=args.title,
            owner=args.owner,
            status=args.status,
            updated=updated,
            next_action=args.next,
            task_file=f"docs/agent-handoff/tasks/{slug}.md",
        ),
    )
    print(f"Created {path}")


def append_handoff(args: argparse.Namespace) -> None:
    ensure_dirs()
    slug = slugify(args.slug)
    path = task_path(slug)
    text = read_text(path)
    updated = now_utc()

    handoff = (
        f"\n\n### {updated} - {args.agent}\n\n"
        f"- Summary: {args.summary.strip()}\n"
        f"- Files: {render_list(args.files)}\n"
        f"- Commands: {render_list(args.commands)}\n"
        f"- Blockers: {render_list(args.blockers)}\n"
        f"- Next: {args.next.strip()}\n"
    )

    text = replace_meta_line(text, "Current Owner", f"`{args.agent}`")
    text = replace_meta_line(text, "Status", f"`{args.status}`")
    text = replace_meta_line(text, "Last Updated", f"`{updated}`")
    text = replace_meta_line(text, "Next Action", f"`{args.next}`")
    text = text.rstrip() + handoff + "\n"
    write_text(path, text)

    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else slug
    update_active_tasks(
        slug,
        TaskRow(
            title=title,
            owner=args.agent,
            status=args.status,
            updated=updated,
            next_action=args.next,
            task_file=f"docs/agent-handoff/tasks/{slug}.md",
        ),
    )
    print(f"Updated {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared handoff helper for Claude Code and Codex.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_task = subparsers.add_parser("new-task", help="Create a new durable task file.")
    new_task.add_argument("--slug", help="Task slug. Defaults to a slugified title.")
    new_task.add_argument("--title", required=True, help="Human-readable title.")
    new_task.add_argument("--owner", default="human", help="Current owner.")
    new_task.add_argument("--status", default="planned", help="Task status.")
    new_task.add_argument("--next", required=True, help="Exact next action.")
    new_task.add_argument("--objective", default="Fill this in before starting implementation.")
    new_task.add_argument("--current-state", default="No session notes yet.")
    new_task.set_defaults(func=create_task)

    handoff = subparsers.add_parser("handoff", help="Append a handoff entry to an existing task.")
    handoff.add_argument("--slug", required=True, help="Task slug.")
    handoff.add_argument("--agent", required=True, help="Agent leaving the handoff.")
    handoff.add_argument("--status", default="active", help="Updated task status.")
    handoff.add_argument("--summary", required=True, help="What changed in this session.")
    handoff.add_argument("--next", required=True, help="Exact next action.")
    handoff.add_argument("--files", action="append", default=[], help="Touched file path. Can be repeated.")
    handoff.add_argument("--commands", action="append", default=[], help="Command or test run. Can be repeated.")
    handoff.add_argument("--blockers", action="append", default=[], help="Blocker or risk. Can be repeated.")
    handoff.set_defaults(func=append_handoff)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
