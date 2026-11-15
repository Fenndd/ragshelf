---
id: T010
title: Build the gold evaluation set
milestone: M3
status: planned
depends_on: [T005]
area:
  - "data/eval/**"
  - "docs/evaluation/gold-set-format.md"
---

# T010 — Build the gold evaluation set

## Goal

Create a labelled query set that measures retrieval and answers independently of chunking.

## Sources

- [Evaluation in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §4](../docs/research/reports/Production%20RAG%20architecture.md)
- [Requirements R2, R3](../docs/requirements.md)

## Scope

In scope: Document the format in `docs/evaluation/gold-set-format.md` (tracked). Write `data/eval/gold.jsonl` (untracked): at least 50 query intents, each in ru, sk, and en; relevant `doc_id`s with page or section spans; a short reference answer; 10–20% unanswerable intents. Include the query types the user actually asks (factual, comparison across documents, definition, method details).

Out of scope: Code for evaluation (T015, T018).

## Acceptance Criteria

1. `gold-set-format.md` defines every field.
2. `gold.jsonl` validates against the format (a check script or test), has ≥50 intents with all three languages, and 10–20% unanswerable.
3. Every referenced `doc_id` exists in `data/library/`.
4. The user has reviewed the set; the review is recorded in Result.

## Checks

- Validation script or test (written in this task; its path recorded in Result).
- Manual: user review.

## Open Questions

- Who writes the queries: the user, or the assistant drafts from the documents and the user corrects them?

## Result

Not started.
