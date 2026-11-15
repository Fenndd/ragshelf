---
id: T007
title: Implement the structure-aware chunker
milestone: M2
status: planned
depends_on: [T006]
area:
  - "src/ragshelf/chunking/**"
  - "tests/chunking/**"
  - "src/ragshelf/cli.py"
---

# T007 — Implement the structure-aware chunker

## Goal

Split documents into heading-aware chunks with deterministic IDs, heading paths, and page spans, sized with the embedder's tokenizer.

## Sources

- [Chunking in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §3](../docs/research/reports/Production%20RAG%20architecture.md)

## Scope

In scope: Chunker per ADR 0002 with parameters from configuration and a version constant; token counts from the harrier tokenizer (tokenizer only, no model load). Each chunk carries ID, text, embedded text (heading path + text), heading path, page span, block types. `ragshelf inspect <doc_id> --chunks` prints chunk count and token-size distribution.

Out of scope: Embedding and storage (T008). LLM-written prefixes and parent/child retrieval (after M3).

## Acceptance Criteria

1. Body text is fully covered: joining chunk texts (minus overlap) reproduces the document body; references are excluded.
2. No chunk exceeds the maximum except a single table, equation, or code block, which is flagged.
3. The same document yields identical chunk IDs on repeated runs; editing one section changes only that section's chunk IDs.
4. Golden tests on fixtures pass; the size distribution over `data/library/` is recorded in Result.

## Checks

- `venv/Scripts/python.exe -m pytest tests/chunking`
- `venv/Scripts/ragshelf.exe inspect <doc_id> --chunks` over the library.

## Open Questions

None

## Result

Not started.
