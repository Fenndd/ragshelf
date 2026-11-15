---
id: T019
title: Rewrite the Streamlit app over the library
milestone: M5
status: planned
depends_on: [T017]
area:
  - "src/ragshelf/app/**"
  - "README.md"
---

# T019 — Rewrite the Streamlit app over the library

## Goal

Provide a thin UI for asking questions over the indexed library.

## Sources

- [Requirements R3, R5](../docs/requirements.md)
- [Layering and generation in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: Question box, cloud/local switch, answer with citation labels linked to an expandable source view (document, page, chunk text), abstention shown plainly, index status (documents, index ID, last ingest). No pipeline logic in the app; markdown from answers rendered without remote images or raw HTML. No uploads to the working directory.

Out of scope: Upload-and-ingest from the UI (candidate follow-up).

## Acceptance Criteria

1. The app starts with `streamlit run` and answers a gold question with working citation expanders.
2. An answer containing a remote image link or HTML is shown as text.
3. The app module imports only library functions (`ragshelf.ask`, status), checked by reading the diff.

## Checks

- `venv/Scripts/streamlit.exe run src/ragshelf/app/streamlit_app.py`, manual walkthrough with screenshots.
- Diff review.

## Open Questions

None

## Result

Not started.
