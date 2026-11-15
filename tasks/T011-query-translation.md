---
id: T011
title: Add query translation to English
milestone: M3
status: planned
depends_on: [T004]
area:
  - "src/ragshelf/retrieve/translate.py"
  - "src/ragshelf/prompts/**"
  - "tests/retrieve/test_translate.py"
---

# T011 — Add query translation to English

## Goal

Translate non-English queries to English before retrieval while keeping the original for the answer language and the trace.

## Sources

- [Query translation row in ADR 0001](../docs/decisions/0001-model-stack.md)
- [Retrieval in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: Language detection of the query (by the LLM response or a light detector chosen in the task and justified in Result), translation through the `ChatClient` with a versioned prompt that returns only the translation, English queries passed through unchanged, failure raises instead of silently using the original.

Out of scope: Multi-query rewriting or HyDE (candidate experiments after the baseline).

## Acceptance Criteria

1. Unit tests with the scripted client cover ru, sk, en pass-through, and failure.
2. On 10 ru and 10 sk gold-set queries through the cloud route, the translations are reviewed and recorded in Result.

## Checks

- `venv/Scripts/python.exe -m pytest tests/retrieve/test_translate.py`
- Manual review of 20 translations.

## Open Questions

None

## Result

Not started.
