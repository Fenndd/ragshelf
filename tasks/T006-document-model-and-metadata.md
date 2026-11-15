---
id: T006
title: Build the document model and metadata extraction
milestone: M2
status: planned
depends_on: [T005]
area:
  - "src/ragshelf/documents/**"
  - "tests/documents/**"
  - "src/ragshelf/cli.py"
---

# T006 — Build the document model and metadata extraction

## Goal

Turn cached parser output into a normalized document with ordered, typed blocks, page numbers, a separated reference list, and metadata.

## Sources

- [Requirements R2, R3, R6](../docs/requirements.md)
- [Chunking and identity in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: `Document` with metadata (title, authors, year, DOI, language) and blocks (heading level, type: paragraph/list/table/equation/code/caption, text, page). Normalization: Unicode NFC, hyphenation across line breaks, repeated running headers and footers. Reference list detected from headings in any language MinerU reports and kept apart from the body. Metadata from MinerU title and author blocks, PDF metadata, a DOI pattern, with sidecar values overriding. `ragshelf inspect <doc_id>` prints metadata and the heading outline.

Out of scope: Chunking (T007). Parsing individual references into fields.

## Acceptance Criteria

1. Golden tests on synthetic Markdown/content-list fixtures check block types, pages, headings, normalization, and reference separation.
2. A sidecar value replaces the extracted value for that field only.
3. `ragshelf inspect` runs for every document in `data/library/`; a table of extracted title, authors, year, DOI for 10 documents is reviewed by the user.

## Checks

- `venv/Scripts/python.exe -m pytest tests/documents`
- `venv/Scripts/ragshelf.exe inspect <doc_id>` on each document.
- Manual: user spot-check of 10 documents, outcome recorded in Result.

## Open Questions

None

## Result

Not started.
