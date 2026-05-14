# Daily Progress - 2026-05-14 - ContextIQ

## Goal

Publish ContextIQ as the second standalone portfolio project.

## Changes

- Prepared ContextIQ for public release with `.gitignore` and `.env.example`.
- Kept local `.env`, coverage, vector index state, processed document cache, and large raw corpus files out of the public repository.
- Removed unused optional eval dependencies that pulled OpenAI-related transitive packages into the lockfile.
- Published ContextIQ as a standalone public repository.
- Featured ContextIQ in the main portfolio README.

## Verification

- `uv run --extra dev pytest -q` passed with 87 tests.
- `uv run --extra dev ruff check .` passed.
- Public file scan confirmed only `data/raw/sample-contract.md` is included from the raw corpus.
- Dependency scan confirmed the source and lockfile no longer include OpenAI, RAGAS, or DeepEval packages.

## Next Task

Define the next project build sequence and keep the daily work review-gated before any commit or push.
