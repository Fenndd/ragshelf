---
id: T014
title: Trace every query
milestone: M3
status: planned
depends_on: [T013]
area:
  - "src/ragshelf/trace.py"
  - "src/ragshelf/retrieve/**"
  - "src/ragshelf/cli.py"
  - "tests/test_trace.py"
  - "docs/data-layout.md"
---

# T014 — Trace every query

## Goal

Record each search as one local JSONL line so retrieval behavior can be inspected and evaluated.

## Sources

- [Evaluation and tracing in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §5](../docs/research/reports/Production%20RAG%20architecture.md)

## Scope

In scope: Trace record: timestamp, configuration hash, index ID, original and translated query, candidate IDs and scores per stage, reranker scores, per-stage latency; later tasks add context IDs, prompt version, model, route, answer, citations, abstention. Written to `data/traces/YYYY-MM-DD.jsonl`; `--no-trace` flag.

Out of scope: A trace viewer.

## Acceptance Criteria

1. One `ragshelf search` appends exactly one valid JSON line with all listed fields.
2. No secret appears in traces (test with a dummy key).
3. docs/data-layout.md documents `data/traces/`.

## Checks

- `venv/Scripts/python.exe -m pytest tests/test_trace.py`
- Run `search` and inspect the new line.

## Open Questions

None

## Result

Not started.
