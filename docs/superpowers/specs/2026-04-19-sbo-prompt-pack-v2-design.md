# Second Brain OS Prompt Pack v2 Design

**Date:** 2026-04-19
**Status:** Draft for review
**Project:** `projects/second-brain-os`
**Reference source:** `https://github.com/dair-ai/Prompt-Engineering-Guide`

## Goal

Upgrade Second Brain OS from generic source summarization to portfolio-aware intelligence extraction.

The new prompt system should make every ingested repo, article, or video answer this question:

> How does this source help Venki build one or more of the 24 portfolio projects?

The first validation target is the DAIR Prompt Engineering Guide. A generated note for that repo should be useful enough to guide prompt design for Second Brain OS, ContextForge, AgentOrchestra, RAGBench Pro, and EvalEngine.

## Problem

The current prompts are primitive. They summarize each source in isolation and produce only:

- Summary
- Key Insights
- Relevance to My Work
- Tags

That is not enough. The output does not know `PORTFOLIO.md`, the current project, project phases, build decisions, reusable prompt patterns, or testing needs. A note can be accurate and still not help build anything.

## Design Principles

Use the DAIR Prompt Engineering Guide as a process reference:

- Start simple, then iterate with experiments.
- Use specific, direct instructions.
- Separate instruction, context, and source content with clear delimiters.
- Break complex tasks into smaller prompt-chain steps.
- Prefer positive output contracts over vague negative constraints.
- Include explicit desired formats and examples where structure matters.

## Approach

Use a portfolio-aware prompt chain instead of one giant summarization prompt.

```text
Raw Source
  -> Source Intelligence Extractor
  -> Portfolio Mapper
  -> Build Implication Extractor
  -> Prompt Pattern Extractor
  -> Helpfulness Evaluator
  -> Obsidian Note Writer
```

This remains simple enough for the current SBO pipeline, but it gives us better control over helpfulness.

## Prompt Pack v2 Files

Create versioned prompts under:

```text
projects/second-brain-os/prompts/v2/
```

Files:

- `repo_intelligence.yaml`
- `article_intelligence.yaml`
- `video_intelligence.yaml`
- `portfolio_mapper.yaml`
- `build_implications.yaml`
- `prompt_patterns.yaml`
- `helpfulness_evaluator.yaml`
- `sbo_ask.yaml`
- `research_report.yaml`

The existing `prompts/*.yaml` can stay as v1 compatibility until the v2 chain is wired.

## Required Context

Every v2 prompt gets structured context, not just `{body}`.

```yaml
portfolio_context:
  current_project:
    id: "00"
    name: "Second Brain OS"
    goal: "Knowledge harness and research agent"
  projects:
    - id: "01"
      name: "ContextForge"
      focus: "context management, token budgeting"
    - id: "02"
      name: "RAGBench Pro"
      focus: "RAG evaluation framework"
source:
  type: "github_repo"
  title: "dair-ai/Prompt-Engineering-Guide"
  url: "https://github.com/dair-ai/Prompt-Engineering-Guide"
  content: "..."
```

Implementation should derive project context from `PORTFOLIO.md` or `config/portfolio_projects.yaml`. The prompt should not hardcode the 24 projects.

## Output Contract

The final Obsidian note should use this structure:

````markdown
# <Source Title>

## Executive Summary

## Why This Matters For The Portfolio

## Project Relevance
| Project | Relevance | How To Use It |
|---|---:|---|

## Techniques To Steal
| Technique | Use In | Implementation Note |
|---|---|---|

## Prompt Patterns
```text
Reusable prompt fragment or pattern.
```

## Build Decisions
- Decision:
  Evidence:
  Apply in:

## Eval Questions
- Question:
  Expected useful answer should include:

## Source Links
- <source url>

## Helpfulness Score
Score: <0-100>
Reasoning:
````

The writer can add frontmatter, tags, and source metadata as the current note writer already does.

## Helpfulness Rubric

Score every generated note out of 100:

| Category | Points | Description |
|---|---:|---|
| Source accuracy | 20 | Captures what the source actually contains without hallucination |
| Portfolio mapping | 20 | Maps to specific portfolio projects and explains why |
| Implementation value | 20 | Produces concrete build decisions or tasks |
| Reusable patterns | 15 | Extracts prompt, architecture, eval, or code patterns |
| Eval readiness | 15 | Produces test questions or acceptance checks |
| Source grounding | 10 | Preserves source URL/path and avoids unsupported claims |

Acceptance threshold:

- `>= 70`: useful enough to keep
- `50-69`: keep but flag for manual review
- `< 50`: write to inbox/review folder or mark as low-quality

## DAIR Validation Scenario

Run:

```bash
sbo run --source github --url https://github.com/dair-ai/Prompt-Engineering-Guide
sbo index
sbo ask "What prompt engineering techniques should we use for Second Brain OS?"
```

Expected generated note qualities:

- Identifies prompt chaining, RAG prompting, ReAct, structured output, prompt eval, and adversarial/factuality guidance.
- Maps DAIR content to at least these projects:
  - Second Brain OS
  - ContextForge
  - RAGBench Pro
  - AgentOrchestra
  - EvalEngine
- Produces at least three concrete prompt patterns.
- Produces at least five eval questions for prompt helpfulness.
- Scores at least `70/100`.

## System Changes

Add `PromptChain` service:

```text
src/second_brain/processing/prompt_chain.py
```

Responsibilities:

- Load v2 YAML prompt definitions.
- Inject source metadata and portfolio context.
- Run chain steps in a deterministic order.
- Return structured `PromptChainResult`.
- Preserve token/cost information from `LLMClient`.

Add `HelpfulnessEvaluator`:

```text
src/second_brain/evals/helpfulness.py
```

Responsibilities:

- Parse v2 note output.
- Score notes using the 100-point rubric.
- Support deterministic unit tests with no LLM calls.
- Later support LLM-as-judge as an optional eval mode.

Update settings:

- Add `PROMPT_VERSION`, defaulting to `v1` for the first test session.
- Allow `PROMPT_VERSION=v2` to opt into the new prompt chain.

Update `Summarizer`:

- Keep v1 behavior when `PROMPT_VERSION=v1`.
- Use v2 chain when `PROMPT_VERSION=v2`.
- Continue to return `ProcessedContent` so the existing pipeline does not need a broad rewrite.

Update CLI:

- Add a command to run prompt evals on a generated note:

```bash
sbo eval prompt <note-path>
```

## Testing Plan

Unit tests:

- v2 prompts load correctly.
- portfolio context is injected.
- prompt chain calls steps in order.
- generated note parser extracts project relevance, build decisions, prompt patterns, eval questions, and score.
- helpfulness scorer returns expected values for high-quality and low-quality fixture notes.

Integration-style local test:

- Use a fixture that represents a trimmed DAIR repo README.
- Run v2 chain with a fake LLM.
- Assert output maps to portfolio projects and scores above threshold.

Manual live test:

- Run DAIR ingestion with Anthropic enabled.
- Inspect note quality.
- Ask vault questions against the indexed result.

## Non-Goals

- Do not build the full LangGraph `sbo research` loop in this slice.
- Do not add MCP tools in this slice.
- Do not fine-tune prompts through automatic prompt optimization yet.
- Do not require live LLM calls for unit tests.

## Rollout Decision

Ship v2 behind `PROMPT_VERSION=v2` first. Test on DAIR, inspect the note, run the helpfulness scorer, and only make v2 the default after the generated note scores at least `70/100`.
