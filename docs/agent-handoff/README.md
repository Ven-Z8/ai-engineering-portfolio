# Agent Handoff System

This repo can be worked on by both Claude Code and Codex. The repo itself is the shared memory.

Do not rely on chat history surviving between sessions. Before starting work, read the task file. Before ending work, leave a handoff entry.

## Goals

- Let Claude and Codex work on the same project without losing context.
- Make handoffs explicit, short, and reviewable in git.
- Keep status in repo files instead of private agent memory.
- Make it easy to resume work after limits, pauses, or model switching.

## Layout

- `docs/agent-handoff/ACTIVE_TASKS.md`: top-level queue and current owner/status.
- `docs/agent-handoff/tasks/<task-slug>.md`: durable task context and session handoffs.
- `docs/agent-handoff/templates/TASK_TEMPLATE.md`: reference template for task files.
- `scripts/agent_handoff.py`: helper for creating tasks and appending handoffs.

## Working Rules

1. Read `ACTIVE_TASKS.md` and the task file before making changes.
2. One durable task file per workstream.
3. Every session must leave a handoff entry before stopping.
4. Handoff entries should say what changed, what is blocked, and the exact next step.
5. If both agents are working in parallel, use separate git branches or worktrees.
6. If a session changes scope, update the task file before doing more work.

## Recommended Workflow

### Start of session

1. Open `docs/agent-handoff/ACTIVE_TASKS.md`.
2. Pick the task you are taking over.
3. Read the linked task file.
4. Update the task owner/status if needed.

### During session

- Keep major decisions in the task file, not only in chat.
- If you discover a blocker, add it immediately.
- If you split work, create another task file instead of burying it in notes.

### End of session

Leave a handoff entry with:

- what you completed
- files touched
- commands/tests run
- blockers or risks
- exact next action for the next session

## Helper Script

Create a task:

```bash
python3 scripts/agent_handoff.py new-task \
  --slug shared-handoff \
  --title "Shared Codex and Claude handoff system" \
  --owner codex \
  --status active \
  --next "Review the workflow and start using it on the first real task"
```

Append a handoff:

```bash
python3 scripts/agent_handoff.py handoff \
  --slug shared-handoff \
  --agent codex \
  --summary "Created the shared handoff scaffold and helper script." \
  --next "Use this on the next real project task and refine based on friction." \
  --files docs/agent-handoff/README.md \
  --files scripts/agent_handoff.py
```

## Branch and Worktree Guidance

For same-repo collaboration, the safest setup is:

- one branch/worktree per active task
- one task file per branch/workstream
- merge only after the task file says the work is ready

If both agents must touch the same task, keep the task file current so the other session can take over without guessing.
