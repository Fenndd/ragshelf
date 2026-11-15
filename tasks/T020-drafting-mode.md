---
id: T020
title: Add the drafting mode
milestone: M5
status: planned
depends_on: [T019]
area:
  - "src/ragshelf/generate/draft.py"
  - "src/ragshelf/prompts/**"
  - "src/ragshelf/cli.py"
  - "src/ragshelf/app/**"
  - "tests/generate/test_draft.py"
---

# T020 — Add the drafting mode

## Goal

Draft an academic paragraph on a topic from the same retrieval pipeline, citing sources as (Author, Year).

## Sources

- [Requirement R4](../docs/requirements.md)

## Scope

In scope: `ragshelf draft "<topic>"` and a UI mode: retrieval as in `ask`, a versioned drafting prompt, citations mapped from `[S<n>]` to (Author, Year) from metadata with the label list kept for checking; same citation validation and abstention.

Out of scope: Reference-list formatting styles.

## Acceptance Criteria

1. Scripted-client tests cover citation mapping and validation.
2. A real draft on a gold topic cites only documents in its context, reviewed by the user.

## Checks

- `venv/Scripts/python.exe -m pytest tests/generate/test_draft.py`
- Manual draft run reviewed by the user.

## Open Questions

None

## Result

Not started.
