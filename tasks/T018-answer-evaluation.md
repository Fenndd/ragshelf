---
id: T018
title: Evaluate answers
milestone: M4
status: planned
depends_on: [T017, T015]
area:
  - "src/ragshelf/eval/**"
  - "src/ragshelf/cli.py"
  - "tests/eval/**"
  - "docs/evaluation/**"
---

# T018 — Evaluate answers

## Goal

Measure faithfulness, citation quality, and abstention on the gold set for both generation routes.

## Sources

- [Evaluation in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §4](../docs/research/reports/Production%20RAG%20architecture.md)

## Scope

In scope: `ragshelf eval answers [--local]`: claim-level faithfulness and citation precision/recall judged by an LLM different from the generator (judge choice and cost recorded in Result; any new model choice goes through an ADR first), abstention accuracy on unanswerable items, answer-language check. Calibrate the judge on 30 items graded by the user. Results in `docs/evaluation/`.

Out of scope: Improving prompts or retrieval (follow-up tasks).

## Acceptance Criteria

1. Judge agreement with the user's 30 grades is computed and recorded.
2. Metrics for the cloud and local routes are recorded with configuration hash and prompt version.

## Checks

- `venv/Scripts/python.exe -m pytest tests/eval`
- `venv/Scripts/ragshelf.exe eval answers` and `--local`
- Manual: user grades 30 answers.

## Open Questions

- Which model serves as judge (needs an ADR if it is not in ADR 0001).

## Result

Not started.
