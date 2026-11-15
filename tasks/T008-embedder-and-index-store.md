---
id: T008
title: Add the embedder and the versioned index store
milestone: M2
status: planned
depends_on: [T007]
area:
  - "src/ragshelf/embed/**"
  - "src/ragshelf/index/**"
  - "src/ragshelf/models/**"
  - "tests/embed/**"
  - "tests/index/**"
  - "tests/fakes.py"
  - "pyproject.toml"
  - "requirements.txt"
---

# T008 — Add the embedder and the versioned index store

## Goal

Store chunks, vectors, and a BM25 index under a versioned index directory that supports upsert and delete per document.

## Sources

- [Storage and models in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Embedding and BM25 rows in ADR 0001](../docs/decisions/0001-model-stack.md)

## Scope

In scope: Install `lancedb`; record the installed version. Embedder for harrier (bf16, batched; passages without prompt, queries with `web_search_query`) with explicit load and unload. Index writer: LanceDB table and `bm25s` index over the same chunk IDs, `manifest.json`, `data/index/current`; upsert and delete by `doc_id`; a new index ID when manifest fields change. A deterministic fake embedder in `tests/fakes.py`. Minimal model lifecycle (load, free, `torch.cuda.empty_cache`).

Out of scope: The `ingest` command and deleting prototype modules (T009). Querying beyond a smoke test (T012).

## Acceptance Criteria

1. `lancedb` installs and imports on Python 3.14 in `venv/`.
2. With the fake embedder: upserting a document twice leaves one copy; deleting removes its rows from both indexes; a manifest change creates a new index directory.
3. A slow test embeds 3 fixture passages with harrier and finds the expected one first for an English and a Russian query.
4. VRAM returns to its pre-load level (±100 MiB) after unload, measured with `nvidia-smi`.

## Checks

- `venv/Scripts/python.exe -m pytest tests/embed tests/index`
- `venv/Scripts/python.exe -m pytest -m slow tests/embed`
- `nvidia-smi --query-gpu=memory.used --format=csv` before load, after load, after unload.

## Open Questions

None

## Result

Not started.
