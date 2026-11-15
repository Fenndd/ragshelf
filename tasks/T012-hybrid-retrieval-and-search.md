---
id: T012
title: Add hybrid retrieval with RRF and the search command
milestone: M3
status: planned
depends_on: [T009, T011]
area:
  - "src/ragshelf/retrieve/hybrid.py"
  - "src/ragshelf/retrieve/fusion.py"
  - "src/ragshelf/cli.py"
  - "tests/retrieve/test_fusion.py"
  - "tests/retrieve/test_hybrid.py"
---

# T012 — Add hybrid retrieval with RRF and the search command

## Goal

Retrieve candidates from dense and BM25 indexes and fuse them by rank.

## Sources

- [Retrieval in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §1](../docs/research/reports/Production%20RAG%20architecture.md)

## Scope

In scope: Dense top-k with the query prompt and BM25 top-k over the current index, fused with RRF (k from configuration); `ragshelf search "<query>"` translates, retrieves, fuses, and prints chunk, document, page, and per-stage ranks.

Out of scope: Reranking (T013), tracing (T014).

## Acceptance Criteria

1. Fusion unit tests: known rank lists produce the expected order; ties and missing items handled.
2. Hybrid test with the fake embedder returns chunks found by only one retriever.
3. `ragshelf search` with a ru, sk, and en query returns results with document and page.

## Checks

- `venv/Scripts/python.exe -m pytest tests/retrieve`
- `venv/Scripts/ragshelf.exe search "..."` in three languages.

## Open Questions

None

## Result

Not started.
