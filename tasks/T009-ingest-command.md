---
id: T009
title: Wire the ingest command and remove the replaced prototype
milestone: M2
status: planned
depends_on: [T008]
area:
  - "src/ragshelf/ingest.py"
  - "src/ragshelf/cli.py"
  - "tests/test_ingest.py"
  - "src/ragshelf/loaders/**"
  - "src/ragshelf/processing/**"
  - "src/ragshelf/embeddings/**"
  - "src/ragshelf/store/**"
  - "pyproject.toml"
  - "requirements.txt"
  - "README.md"
  - "data/README.md"
  - "docs/decisions/0001-model-stack.md"
---

# T009 — Wire the ingest command and remove the replaced prototype

## Goal

Make `ragshelf ingest` build and update the index for the whole library, and delete the prototype modules it replaces.

## Sources

- [Requirements R1, R6, R7](../docs/requirements.md)
- [ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: `ragshelf ingest`: scan → parse (cached) → documents → chunks → embed (one model load for the batch) → write; reports added/updated/removed/skipped and per-stage time. Delete `loaders/`, `processing/`, `embeddings/`, `store/`; remove `faiss-cpu`, `pymupdf`, `pdfplumber`, `langdetect`, `tiktoken`; refresh `requirements.txt`. README notes that the Streamlit app is unavailable until T019. Check `onnxruntime` providers after removing `pymupdf` and update ADR 0001's note.

Out of scope: Retrieval and generation.

## Acceptance Criteria

1. A full run over `data/library/` completes and every document has chunks in the index.
2. A second run reports 0 parsed and 0 embedded.
3. Editing one sidecar re-indexes that document only; deleting a file removes its chunks.
4. The deleted packages are absent from `pyproject.toml`, `requirements.txt`, and `venv/`.
5. `onnxruntime.get_available_providers()` includes `DmlExecutionProvider`.
6. An integration test with fakes covers add, change, delete, and skip.

## Checks

- `venv/Scripts/python.exe -m pytest tests/test_ingest.py`
- `venv/Scripts/ragshelf.exe ingest` twice, then after editing and deleting one test document.
- `venv/Scripts/python.exe -c "import onnxruntime as o; print(o.get_available_providers())"`

## Open Questions

None

## Result

Not started.
