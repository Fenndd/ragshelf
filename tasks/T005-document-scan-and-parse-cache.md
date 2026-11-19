---
id: T005
title: Add the document scan and the parse cache
milestone: M2
status: done
depends_on: [T003]
area:
  - "src/ragshelf/parse/**"
  - "tests/parse/**"
  - "src/ragshelf/cli.py"
  - "tests/test_cli.py"
  - "pyproject.toml"
  - "tasks/T005-document-scan-and-parse-cache.md"
  - "tasks/T004-llm-clients.md"
  - "ROADMAP.md"
  - "STATUS.md"
  - "docs/data-layout.md"
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

Planning clarification (2026-11-17): after accepting T004, the user instructed continuation with T005. Independent, non-destructive implementation and checks may proceed while the migration question below remains pending. This explicitly permits starting this part of T005 before that open question is resolved, as a task-specific clarification to the normal ready/start sequence in TASK_FORMAT.md. Read-only inventory of the existing layout and file hashes, implementation, and checks with synthetic fixtures are authorized. Moving originals, conversion of existing metadata, and deletion of prototype outputs remain subject to the separate migration confirmation. The migration scope and acceptance criteria are unchanged; T005 cannot be accepted as complete until the migration is authorized and criterion 4 is verified. The area now also names CLI integration, its tests, and the task/status documentation. Later on the same date, the user approved the concrete migration plan recorded under Open Questions; the earlier separation of implementation from migration approval remains part of the planning history.

Runtime clarification (2026-11-17): the installed MinerU 4.2.2 kit uses local `standard` parsing for PDF/images and native `flash` dispatch for Office/HTML/EPUB. The implementation follows that installed local dispatch rather than forcing unsupported `standard` parsing for every format; no remote parser is used. The adapter directly uses DocVortex native HTML conversion and asset materialization, so `docvortex` is now an explicit dependency (the installed/pinned version was already 0.6.22). The task area includes `pyproject.toml`. No acceptance criterion changes.

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

None. The user approved the concrete migration plan on 2026-11-17 after a read-only layout/hash inventory: preserve 21 unique PDFs and their metadata as byte-preserved sidecars at the library root; verify hashes before deleting four duplicate PDF/metadata pairs, 12 prototype-derived files, the empty old manifest, and 35 legacy directories. `data/raw/` and `data/experiments/` are outside that approved plan. Execution and verification are recorded separately below.

## Result

### Implementation completion — 2026-11-18

T005 is `review`: all five acceptance criteria are verified and user acceptance is pending. The user reported manually deleting the 35 empty legacy directories after the agent's deletion command was rejected by automatic approval review. A fresh filesystem check confirmed that all 31 numbered inbox paths and all four article paths are absent; no additional legacy article directories were found in the library.

Verification after manual cleanup: 21 PDFs and 21 corresponding sidecars remain, with all 42 SHA-256 values matching the original migration evidence and all 21 document hashes unique. The cache, raw, and experiments directories remain present. A fresh-process `parse_library(load_settings())` check returned **21 hits, 0 parsed, 0 failed**, with neither `torch` nor `mineru.parser` imported. This also validates the cached bundle checksums through the normal hit path. No source code changed and no model parsing or broad test rerun was required for this directory-only cleanup. The previous dated test, runtime, and independent-review evidence below remains applicable.

The earlier cleanup blocker is resolved. This records implementation completion, not user acceptance; the message reporting directory removal does not accept T005. T005 remains in `review` pending user acceptance. The T005 changes are committed locally on 2026-11-18; T006 has not started, and no push was requested or performed.

### Earlier partial result — 2026-11-17

At this checkpoint T005 was `blocked` solely because 35 empty legacy directories remained after automatic approval review rejected their deletion. Criteria 1, 2, 3, and 5 were verified; criterion 4 was partial. The following dated record preserves that checkpoint and is superseded by the completion evidence above.

Implemented: recursive deterministic scanning with path-based identity and SHA-256; format-specific local MinerU dispatch and UTF-8 text passthrough; a parser-specific cache independent of later embedding/retrieval settings; checksum manifests, output validation, a batch writer lock, staged publication, and runtime release; `ingest --parse-only` reporting and exit status; fake-parser tests and a real-runtime synthetic smoke test. HTML cache identity includes the source context and consumed local resources. Source and resource changes are checked before publishing and when accepting a hit. The direct DocVortex dependency and CLI integration are included in the task area.

Migration: the user approved the concrete plan after a read-only inventory. The file portion is verified: 21 unique PDFs and 21 byte-preserved metadata sidecars (`<complete original filename>.metadata.json`) were placed at the library root; all 42 source/destination hashes were checked before deleting four duplicate PDF/metadata pairs, 12 derived files, and the empty old manifest. `data/raw/` and `data/experiments/` were excluded. **Criterion 4 remains partial:** automatic approval review rejected deletion of the 35 empty legacy directories, and the migration agent stopped; those directories remain (31 `inbox/<N>/` and four `library/article_<N>/`). Local evidence: `data/migration-evidence/T005-2026-11-17.json`, status `files_migrated_verified_empty_directory_cleanup_blocked`. The retained files total 24,002,856 bytes and removed files total 4,082,110 bytes; `raw/`, `experiments/`, and `index/` fingerprints were unchanged. The rejection is a tool/policy limitation after user authorization, not a missing user decision.

| Check | Result |
| --- | --- |
| Parent baseline: `venv/Scripts/python.exe -B -m pytest -p no:cacheprovider` | 96 passed in 30.91 s, before T005 implementation |
| Parent final fast suite: same command | 124 passed, 1 slow test deselected in 16.00 s, after both P2 fixes |
| Synthetic PDF + HTML through the installed local runtime and CLI | First run: 2 parsed; second run: 2 hits. Synthetic text and `page_idx` checked |
| `venv/Scripts/python.exe -B -m pytest tests/parse/test_runtime.py -m slow -p no:cacheprovider` | 1 passed in 29.62 s |
| Independent final `venv/Scripts/python.exe -m pytest tests/parse tests/test_cli.py -m "not slow" -q` | 38 passed, 1 deselected |
| `venv/Scripts/python.exe -m pip check` | `No broken requirements found.` |
| `venv/Scripts/ragshelf.exe ingest --parse-only` on the migrated library, first run | Exit 0; 0 hits, 21 parsed, 0 failed in 917.8 s |
| Same command, unchanged second run | Exit 0; 21 hits, 0 parsed, 0 failed in 1.5 s; stderr empty and no model-load markers |
| Fresh-process cache-hit guard with `mineru.parser.parse` configured to fail if called | 21 hits; neither `torch` nor `mineru.parser` imported |
| Content-free cache validation against original PDF page bounds | 21 valid bundles, 244 checksummed artifacts including 202 assets, 9,334 content items; all `page_idx` values in original-PDF bounds |
| Change-isolation and fake-parser checks in the focused suite | Criteria 2 and 5 verified: a changed source causes only its own miss; scanning, hashing, and parser-key behavior covered |

The 21 PDFs contain 1,297 physical pages; 1,283 pages have extracted content. The parent also independently reran the actual `parse_library` in a fresh process: 21 hits, 0 parsed, 0 failed, with neither `torch` nor `mineru.parser` imported. A parent layout check confirmed 21 PDFs, 21 sidecars, zero files in `inbox/`, 31 empty inbox directories, and four empty article directories. No active parsing workspaces remained after verification. GPU use was approximately 1,003 MiB before the batch, 893 MiB after parsing, and 872 MiB of 6,144 MiB after verification. These post-process measurements do not establish in-process VRAM residency immediately after `close()`; unit tests verify release calls and the real close path completed successfully. Local ignored logs and the summary are under `data/cache/t005-verification/`. The content-free pypdf page-bound diagnostic reported `Ignoring wrong pointing object 1610 (offset 0)`; the documents remained readable and MinerU reported no errors. These checks validate cache structure and page bounds; they do not measure extraction completeness or semantic quality, and the real documents' semantic content was not inspected.

Implementation, approved migration, and independent review were requested at **Tier 4, GPT-6 Astra / high**, because cache integrity, persisted data, and destructive migration require careful verification.
Independent review was requested at **Tier 4, GPT-6 Astra / high**, because incorrect cache identity can reuse stale persisted data. It found an HTML/CSS identity defect (P1): the first fix tracks the native converter's consumed dependencies and source context. Two P2 follow-ups were also corrected: a remote HTML base no longer causes an unused local file to invalidate the cache, and hit validation now rechecks input/resource identity. The original installed-MinerU HTML reproduction then confirmed distinct correct source contexts, two unchanged hits, and one parse plus one hit after editing one dependency. The final independent review found no remaining supported defects and passed the focused 38-test suite. Its scope covered source modules, CLI, tests, and installed APIs; it did not independently execute the full-library GPU parse or migration. The HTML dependency adapter uses a private DocVortex conversion seam; the DocVortex version is part of the cache key and native-runtime tests cover the current installed path. This bounded documentation update was requested at **Tier 2, GPT-6.1 Sol / medium** with the implementation/check contract supplied. Requested model/effort settings are recorded; execution settings and workflow token metrics are not exposed.

Remaining at the 2026-11-17 checkpoint: resolve the automatic-review tool limitation for the 35 empty legacy directories, verify criterion 4, then submit T005 for user review. That cleanup was subsequently verified on 2026-11-18 as recorded above. No further broad check cycle is pending. T006 depends on T005 being `done` and has not started. No commit or push was performed as part of T005.

### Acceptance — 2026-11-18

The user accepted T005 in chat on 2026-11-18 ("Принять T005") after the implementation-completion evidence above: all five acceptance criteria verified, the independent review closed, and the migration cleanup confirmed. T005 is `done`. This unblocks T006; T010 stays `planned` because of its own open question about who writes the gold-set queries.
