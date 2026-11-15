---
id: T016
title: Assemble the answer context
milestone: M4
status: planned
depends_on: [T013]
area:
  - "src/ragshelf/context.py"
  - "tests/test_context.py"
---

# T016 — Assemble the answer context

## Goal

Turn reranked chunks into a bounded, ordered, labelled context that marks document text as untrusted data.

## Sources

- [Retrieval and generation in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §1, §5](../docs/research/reports/Production%20RAG%20architecture.md)

## Scope

In scope: Deduplicate, merge adjacent chunks of one document, enforce a token budget from configuration, order by document and position, label `[S1]…[Sn]` with title, authors, year, page, and wrap each in delimiters. Return the label→chunk map for citation checking.

Out of scope: The prompt and the model call (T017).

## Acceptance Criteria

1. Unit tests cover dedupe, merging, budget truncation, ordering, and labels.
2. Delimiter-like text inside a chunk is escaped so a chunk cannot close its own delimiter.

## Checks

- `venv/Scripts/python.exe -m pytest tests/test_context.py`

## Open Questions

None

## Result

Not started.
