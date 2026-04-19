# Second Brain OS

> GitHub repos, YouTube transcripts, docs, feeds — summarized daily, wired into Obsidian, queryable on demand.

**Portfolio Project #0** — the knowledge harness that runs across all 24 AI portfolio projects.

---

## What it does

Second Brain OS ingests your tracked sources every morning, processes them through Claude, and writes structured Obsidian notes to your vault. It's a harness — not an archiver. Every note stores a `content_hash` and staleness clock. The system knows what it knows and when to re-fetch.

- **GitHub repos** — README + commit history + structure preview → structured note
- **YouTube videos** — transcript extraction → summary + key insights
- **Web articles** — content extraction, paywall detection → article note
- **RSS feeds** — HN, Anthropic blog, research feeds → article notes
- **Daily briefing** — pipeline run summary written to `01-Daily/YYYY-MM-DD.md`

---

## Install

```bash
git clone https://github.com/venkatesh/second-brain-os
cd second-brain-os
uv sync --extra dev
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and VAULT_PATH
```

---

## Quickstart

```bash
# 1. Scaffold your vault
sbo vault setup

# 2. Add sources
sbo add github https://github.com/langchain-ai/langgraph
sbo add youtube https://www.youtube.com/watch?v=...
sbo add feed https://news.ycombinator.com/rss

# 3. Run
sbo run

# 4. Check status
sbo status
```

---

## CLI reference

```
sbo run                          # full pipeline from sources.yaml
sbo run --source github --url U  # single source
sbo run --dry-run                # fetch + summarize, no vault writes
sbo add github <url>
sbo add youtube <url>
sbo add feed <url>
sbo add web <url>
sbo fetch --url <url>            # force re-fetch (coming soon)
sbo status                       # last run stats
sbo vault setup                  # scaffold vault folders
sbo config                       # open sources.yaml in $EDITOR
```

---

## Architecture

```
config/sources.yaml
       │
       ▼
  Pipeline Runner (asyncio.gather — parallel agents)
  ├── GitHubAgent   ── README + structure → RawContent
  ├── YouTubeAgent  ── transcript → RawContent
  ├── WebAgent      ── article extraction → RawContent
  └── RSSAgent      ── feed items → RawContent[]
       │
       ▼ ContextBudget.fit() ← enforces 8k token limit before every call
       │
       ▼
  Summarizer (Claude claude-sonnet-4-6)
  └── structured prompts → summary + insights + tags
       │
       ▼
  ProjectMapper ── keyword intersection → portfolio project links
       │
       ▼
  NoteWriter ── writes to 04-Resources/{repos,videos,articles}/
  DailyNote  ── writes to 01-Daily/YYYY-MM-DD.md
  StateStore ── SQLite dedupe + run log
```

**Portfolio signals:**
- `ContextBudget` — context engineering: every LLM call is budgeted before it fires
- `asyncio.gather` — 4 agents run in parallel, isolated failure handling
- Cost tracking — every LLM call tracked to $0.0001 precision
- Harness thinking — `content_hash` detects stale knowledge, never re-processes unchanged content

---

## Cost

Typical daily run (15 sources): ~$0.06 | ~18,000 tokens

---

## Vault structure

```
vault/
├── 00-Inbox/          ← fallback when API unavailable
├── 01-Daily/          ← YYYY-MM-DD.md daily briefings
├── 02-Projects/       ← one folder per portfolio project
├── 03-Research/       ← research topics
├── 04-Resources/
│   ├── repos/         ← GitHub notes
│   ├── videos/        ← YouTube notes
│   └── articles/      ← web + RSS notes
├── 05-Learning/
├── 06-Career/
└── 07-Meta/
    ├── MOC-Home.md
    └── pipeline-log.md
```

---

## Development

```bash
make test       # run unit tests
make lint       # ruff check
make demo       # dry run (no vault writes)
```
