---
id: T005
title: Add the document scan and the parse cache
milestone: M2
status: planned
depends_on: [T003]
area:
  - "src/ragshelf/parse/**"
  - "tests/parse/**"
  - "data/README.md"
  - "README.md"
---

# T005 — Add the document scan and the parse cache

## Goal

Find every document under `data/library/`, identify it by path and content hash, and parse it with MinerU at most once per content and parser setting.

## Sources

- [Document identity and incremental ingestion in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [MinerU row and consequences in ADR 0001](../docs/decisions/0001-model-stack.md)

## Scope

In scope: Scan `data/library/` for files MinerU accepts plus `.md`/`.txt` (passed through without MinerU); compute `doc_id` and sha256. Run MinerU in process (`mineru-kit parse`, tier `standard`, never `--remote`) for documents without a cache entry, write Markdown and the content list with page indexes under `data/cache/parse/<hash>/<parser-key>/`, free GPU memory after the batch. `ragshelf ingest --parse-only` exposes this step. Migrate the prototype layouts: move originals from `data/inbox/<N>/` and `data/library/article_<N>/` to `data/library/`, convert `metadata.json` to sidecars, detect duplicates by hash, and remove the prototype's derived files — only after the user confirms (see Open Questions).

Out of scope: Building the document model, metadata extraction (T006).

## Acceptance Criteria

1. A second `--parse-only` run with no changes reports every document as a cache hit and does not start MinerU.
2. Changing a file's bytes produces one cache miss for that file only.
3. Cache entries contain Markdown and a content list with page indexes.
4. After migration, `data/library/` holds each original once with its sidecar, and no `article_<N>/` or `inbox/<N>/` folders remain.
5. Unit tests cover scanning, hashing, and cache-key logic with a fake parser.

## Checks

- `venv/Scripts/python.exe -m pytest tests/parse`
- `venv/Scripts/ragshelf.exe ingest --parse-only` twice; compare reported cache hits.
- Listing of `data/library/` before and after migration, with file hashes.

## Open Questions

- Confirm the migration of `data/inbox/` and `data/library/article_*` (moving originals, deleting prototype outputs such as `chunks.json`, `embeddings.npy`, logs).

## Result

Not started.
