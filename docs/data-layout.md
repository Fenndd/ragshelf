# data/

The repository-root `data/` directory holds local documents and everything derived from them. Everything under `data/` is ignored by Git: the documents are third-party copyrighted material, and the derived files (extracted text, chunks, embeddings, logs) contain their text. This layout description lives under `docs/`.

| Path | Contents |
| --- | --- |
| `library/` | Originals, scanned recursively by `ragshelf ingest --parse-only`. A sidecar is named `<complete original filename>.metadata.json`, for example `original.pdf.metadata.json`. JSON sidecars are not parsed as originals. T005 migration placed 21 unique PDFs and 21 byte-preserved sidecars at the root. |
| `cache/parse/<content-sha256>/<parser-key>/` | Reusable parse bundles: `markdown.md`, `content_list.json`, `manifest.json`, and any materialized assets. |
| `cache/parse/.parse.lock` | Operating-system lock used to serialize parsing batches. |
| `inbox/<N>/`, `library/article_<N>/` | Retired prototype paths. The user manually removed the 35 empty directories; their absence was verified on 2026-11-18. |
| `index/` | Reserved for persisted vector indexes; full indexing is [T009](../tasks/T009-ingest-command.md). |
| `raw/` | Collected originals not yet queued for ingestion; excluded from the T005 migration. |
| `experiments/chunking/` | Per-document outputs of the removed prototype script `chunk_experiment.py`, kept as reference; excluded from the T005 migration. |
| `experiments/problem-cases/` | Documents on which extraction, reference splitting, or clustering failed, grouped by the problem observed; excluded from the T005 migration. |
| `cache/t005-verification/` | Local ignored logs and content-free validation summary for the completed 21-document parse and unchanged cache-hit rerun. |
| `migration-evidence/T005-2026-11-17.json` | Local, ignored migration evidence containing file/hash checks and the historical cleanup blocker. The subsequent 2026-11-18 cleanup verification is recorded in T005. |

## Parse cache

The content hash identifies the original bytes; the parser key hashes a descriptor of the effective format, parser/runtime versions, local parser settings, and rendering settings. HTML additionally records source location and consumed local resource identities. The parser key is independent of embedding, chunking, retrieval, and LLM settings. Identical inputs can reuse a bundle when their descriptors agree.

`content_list.json` contains records with nonnegative, zero-based `page_idx` values. UTF-8 `.md` and `.txt` pass through as text with logical page index 0; an empty text input produces an empty content list. `manifest.json` records the schema version, source hash, parser descriptor/key, and SHA-256 of each bundle artifact. Cache reuse validates these checksums, Markdown encoding, content-list page indexes, and unchanged inputs.

A miss parses a snapshot in a temporary sibling workspace and publishes a completed, validated bundle. A damaged existing bundle is preserved under an `.invalid-...` sibling name before replacement. Old content/parser versions are retained; T005 does not implement cache garbage collection. See [T005](../tasks/T005-document-scan-and-parse-cache.md) for checks and remaining acceptance work.

## Migration state

The approved file migration verified all 42 retained file hashes (21 PDFs and 21 metadata sidecars), then removed four duplicate original/metadata pairs, 12 prototype-derived files, and the empty old index manifest. The retained files total 24,002,856 bytes; removed files total 4,082,110 bytes. Fingerprints of `raw/`, `experiments/`, and the remaining `index/` state were unchanged. After automatic approval review blocked agent deletion, the user manually removed the 31 `inbox/<N>/` and four `library/article_<N>/` empty directories. Verification on 2026-11-18 confirmed that all 35 paths are absent, all 42 retained hashes still match the original migration evidence, and all 21 documents remain cache hits. Migration criterion 4 is verified.

The prototype store expects the retired `article_<N>/` document inputs and is no longer usable over this migrated layout. Its replacement and removal remain part of [T009](../tasks/T009-ingest-command.md); T005 supplies parsing, not a searchable index.
