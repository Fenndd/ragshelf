---
id: T015
title: Evaluate retrieval and record the baseline
milestone: M3
status: planned
depends_on: [T010, T014]
area:
  - "src/ragshelf/eval/**"
  - "src/ragshelf/cli.py"
  - "tests/eval/**"
  - "docs/evaluation/**"
---

# T015 — Evaluate retrieval and record the baseline

## Goal

Measure retrieval per stage on the gold set and record the first baseline.

## Sources

- [Evaluation in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §4](../docs/research/reports/Production%20RAG%20architecture.md)

## Scope

In scope: `ragshelf eval retrieval`: runs every gold query (each language), maps chunks to labelled document/page spans, computes recall@50 before reranking and recall@5/10, MRR, nDCG@10 for dense, BM25, fused, reranked; results saved with configuration hash and index ID; comparison against a saved baseline. Baseline and observations in `docs/evaluation/baseline.md` (metrics only, no document text).

Out of scope: Tuning parameters (follow-up tasks based on the baseline).

## Acceptance Criteria

1. Metric functions are unit-tested on hand-computed examples.
2. A full run produces per-stage, per-language metrics.
3. `docs/evaluation/baseline.md` records the numbers, configuration hash, and index ID.

## Checks

- `venv/Scripts/python.exe -m pytest tests/eval`
- `venv/Scripts/ragshelf.exe eval retrieval`

## Open Questions

None

## Result

Not started.
