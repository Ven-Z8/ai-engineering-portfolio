# Skills HUD

Local macOS window that surfaces every Claude Code skill installed on this machine and how often you actually invoke each one.

The point: you have many skills. You don't know which ones earn their slot. This shows you in one screen.

## How it works

- **Installed skills** are discovered by scanning `~/.claude/plugins/**/skills/*/SKILL.md` and parsing the YAML frontmatter (`name`, `description`).
- **Usage** is recovered from `~/.claude/projects/**/*.jsonl` — every `Skill` tool invocation in your session history is counted, and a `last_used` timestamp is kept.
- A small FastAPI server serves the data at `http://127.0.0.1:8731/api/skills`.
- PyWebView wraps that in a real macOS window. No browser tab, no Electron, no signing.

No network calls. No telemetry. Read-only over data that already exists on your disk.

## Run

```bash
uv sync
uv run skills-hud
```

A native window opens with a sortable table:

- **Skill** — `plugin:name` (e.g. `superpowers:brainstorming`)
- **Source** — which plugin and version it came from
- **30d** — invocations in the last 30 days
- **All-time** — every invocation found in session logs
- **Last used** — relative timestamp
- **What it does** — frontmatter description

Filter input narrows by any column. The "Never used" checkbox shows only skills with zero recorded invocations — the ones to either learn or uninstall.

## Headless mode

```bash
uv run skills-hud-serve
```

Runs only the FastAPI server (no window). Useful for debugging the parser or wiring the data into another UI.

## Files

```
skills_hud/
  scanner.py    # finds SKILL.md files, parses frontmatter
  usage.py      # parses session JSONL, counts Skill tool calls
  server.py     # FastAPI app + /api/skills endpoint
  __main__.py   # PyWebView shell
web/
  index.html
  app.js        # sortable table, filter, "never used" toggle
```
