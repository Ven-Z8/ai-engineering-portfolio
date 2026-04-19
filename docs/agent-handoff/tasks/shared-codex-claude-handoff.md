# Shared Codex and Claude handoff system

- Task: `shared-codex-claude-handoff`
- Current Owner: `codex`
- Status: `active`
- Last Updated: `2026-04-19 00:05 UTC`
- Next Action: `Confirm the real project or workstream for this session; if it is not the handoff workflow itself, create a dedicated task file with python3 scripts/agent_handoff.py new-task before implementation.`

## Objective

Create a repo-local handoff workflow that both Codex and Claude can use across separate sessions.

## Current State

Initial scaffold created for shared task tracking and handoff logging.

## Working Agreements

- Keep important decisions here.
- Leave a handoff entry before stopping.
- Prefer exact next steps over vague summaries.

## Important Files

- Add files that matter for this task.

## Risks / Blockers

- None yet.

## Session Handoffs

### 2026-04-18 23:01 UTC - codex

- Summary: Added a shared handoff workflow under docs/agent-handoff and a helper script for creating tasks and logging handoffs.
- Files: docs/agent-handoff/README.md, docs/agent-handoff/ACTIVE_TASKS.md, docs/agent-handoff/templates/TASK_TEMPLATE.md, scripts/agent_handoff.py
- Commands: python3 scripts/agent_handoff.py new-task ..., python3 scripts/agent_handoff.py handoff ...
- Blockers: None
- Next: Open docs/agent-handoff/README.md, confirm the workflow fits how you want to work, and then use it for the next real project task.

### 2026-04-19 00:05 UTC - codex

- Summary: Read the workspace guidance and handoff docs, confirmed the repo rules, and verified that the only tracked task is still the shared Codex/Claude handoff workflow rather than a project-specific workstream.
- Files: docs/agent-handoff/tasks/shared-codex-claude-handoff.md, docs/agent-handoff/ACTIVE_TASKS.md
- Commands: sed -n '1,220p' CLAUDE.md, sed -n '1,220p' AGENTS.md, sed -n '1,260p' docs/agent-handoff/README.md, sed -n '1,260p' docs/agent-handoff/ACTIVE_TASKS.md, sed -n '1,220p' second-brain/INDEX.md, python3 scripts/agent_handoff.py handoff ...
- Blockers: No project-specific handoff task is tracked yet.
- Next: Confirm the real project or workstream for this session; if it is not the handoff workflow itself, create a dedicated task file with python3 scripts/agent_handoff.py new-task before implementation.

