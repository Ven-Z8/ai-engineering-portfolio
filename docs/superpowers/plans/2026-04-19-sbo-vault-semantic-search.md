# SBO Vault Semantic Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a vault-first semantic search foundation to Second Brain OS through `sbo index` and `sbo ask`.

**Architecture:** A local embedding provider wraps Sentence Transformers with EmbeddingGemma prompts, while `VaultIndex` chunks markdown files from `Brain/` and stores/query vectors through a small Chroma-compatible adapter. CLI commands call these services without invoking external web research.

**Tech Stack:** Python 3.12, Typer, SQLite, ChromaDB, Sentence Transformers, EmbeddingGemma, Anthropic SDK.

---

## File Map

- Create `src/second_brain/embeddings/provider.py`: local embedding provider with query/document prompt modes.
- Create `src/second_brain/vault/index.py`: markdown chunking, hash tracking, Chroma-backed indexing/search.
- Create `src/second_brain/research/ask.py`: vault-first answer synthesis service.
- Modify `src/second_brain/core/settings.py`: add embedding/vector settings.
- Modify `src/second_brain/core/db.py`: add indexed file tracking.
- Modify `src/second_brain/cli/main.py`: add `sbo index` and `sbo ask`.
- Modify `pyproject.toml`: add `chromadb`, `sentence-transformers`, `langchain`, and `langgraph`.
- Test `tests/unit/test_embedding_provider.py`: prompt routing and dimensions.
- Test `tests/unit/test_vault_index.py`: chunking, indexing, querying, unchanged-file skipping.
- Test `tests/unit/test_ask.py`: answer prompt uses vault evidence and handles no results.
- Test `tests/unit/test_cli.py`: index and ask commands call service layer.

## Tasks

- [ ] Add failing tests for embedding provider prompt modes.
- [ ] Implement embedding provider with lazy `sentence_transformers` import.
- [ ] Add failing tests for markdown chunking and index metadata.
- [ ] Implement `VaultIndex` with injectable collection/embedding dependencies.
- [ ] Add SQLite indexed-file helpers.
- [ ] Add failing tests for `sbo index` and `sbo ask`.
- [ ] Implement CLI commands.
- [ ] Add dependencies and sync environment.
- [ ] Run focused tests, full unit suite, and ruff.

## Execution Note

Inline execution is chosen for this session because the user explicitly approved building now and the first milestone is tightly scoped.
