# Roadmap

Milestones in order. Task format and statuses: [TASK_FORMAT.md](docs/engineering/TASK_FORMAT.md). Requirements: [docs/requirements.md](docs/requirements.md). Architecture: [ADR 0001](docs/decisions/0001-model-stack.md), [ADR 0002](docs/decisions/0002-pipeline-architecture.md).

## M1 — Clean base

Goal: The package has no dead prototype code, a CLI entry point, a test harness, typed configuration, and working cloud and local LLM clients.

Exit criteria:
1. `legacy/`, the clustering modules, and `scripts/process_sources.py` are absent from the tree.
2. `ragshelf --help` lists `ingest`, `search`, `ask`, `eval`; `pytest` passes.
3. One real request through the new cloud client and one through the local client each return an answer, recorded in T004's Result.

| Task | Title | Depends on | Status |
| --- | --- | --- | --- |
| [T001](tasks/T001-remove-dead-prototype-code.md) | Remove dead prototype code | — | done |
| [T002](tasks/T002-cli-and-test-harness.md) | Add the CLI entry point and test harness | T001 | done |
| [T003](tasks/T003-typed-configuration.md) | Add typed configuration | T002 | done |
| [T004](tasks/T004-llm-clients.md) | Replace the LLM client with cloud and local clients | T003 | planned |

## M2 — Persistent incremental index

Goal: `ragshelf ingest` turns every document in `data/library/` into a versioned LanceDB + BM25 index with citations metadata, and re-runs only touch changed documents.

Exit criteria:
1. `ragshelf ingest` indexes every document in `data/library/` and prints added/updated/removed/skipped counts.
2. A second run with no changes reports 0 parsed and 0 embedded.
3. Changing, adding, or deleting a document changes exactly that document's chunks.
4. `data/index/<id>/manifest.json` records embedder, chunker, parser, and configuration hash.
5. The prototype loader, chunker, embedders, and store are deleted.

| Task | Title | Depends on | Status |
| --- | --- | --- | --- |
| [T005](tasks/T005-document-scan-and-parse-cache.md) | Add the document scan and the parse cache | T003 | planned |
| [T006](tasks/T006-document-model-and-metadata.md) | Build the document model and metadata extraction | T005 | planned |
| [T007](tasks/T007-structure-aware-chunker.md) | Implement the structure-aware chunker | T006 | planned |
| [T008](tasks/T008-embedder-and-index-store.md) | Add the embedder and the versioned index store | T007 | planned |
| [T009](tasks/T009-ingest-command.md) | Wire the ingest command and remove the replaced prototype | T008 | planned |

## M3 — Retrieval with an evaluation baseline

Goal: `ragshelf search` returns reranked, cited chunks for Russian, Slovak, and English queries, and retrieval quality is measured on a gold set.

Exit criteria:
1. `ragshelf search "<query>"` prints the top chunks with document, page, and per-stage scores.
2. The gold set holds at least 50 query intents in ru, sk, and en, 10–20% unanswerable.
3. `ragshelf eval retrieval` reports recall@50 before reranking and recall@5/10, MRR, nDCG@10 per stage; the baseline is recorded in `docs/evaluation/`.
4. Every search appends a trace record to `data/traces/`.

| Task | Title | Depends on | Status |
| --- | --- | --- | --- |
| [T010](tasks/T010-gold-evaluation-set.md) | Build the gold evaluation set | T005 | planned |
| [T011](tasks/T011-query-translation.md) | Add query translation to English | T004 | planned |
| [T012](tasks/T012-hybrid-retrieval-and-search.md) | Add hybrid retrieval with RRF and the search command | T009, T011 | planned |
| [T013](tasks/T013-reranker-and-model-lifecycle.md) | Add the reranker and the model lifecycle | T012 | planned |
| [T014](tasks/T014-query-tracing.md) | Trace every query | T013 | planned |
| [T015](tasks/T015-retrieval-evaluation.md) | Evaluate retrieval and record the baseline | T010, T014 | planned |

## M4 — Grounded answers

Goal: `ragshelf ask` answers in the query's language with validated citations, abstains when evidence is missing, and answer quality is measured.

Exit criteria:
1. `ragshelf ask` cites only `[S<n>]` labels present in its context and lists the cited documents and pages.
2. On the gold set's unanswerable items the system abstains; the rate is reported by `ragshelf eval answers`.
3. Faithfulness, citation precision/recall, and abstention accuracy are recorded in `docs/evaluation/` for the cloud route and the local route.

| Task | Title | Depends on | Status |
| --- | --- | --- | --- |
| [T016](tasks/T016-context-assembly.md) | Assemble the answer context | T013 | planned |
| [T017](tasks/T017-grounded-answers.md) | Generate grounded answers with citations and abstention | T016, T014 | planned |
| [T018](tasks/T018-answer-evaluation.md) | Evaluate answers | T017, T015 | planned |

## M5 — Interface and cleanup

Goal: The Streamlit app works over the indexed library, the drafting mode exists, and no prototype code or unused dependency remains.

Exit criteria:
1. The Streamlit app answers a question over the library with clickable citations and shows ingest status.
2. The drafting mode produces a paragraph with (Author, Year) citations taken from document metadata.
3. `pyproject.toml` lists only imported packages; README, data/README, STATUS reflect the final layout.

| Task | Title | Depends on | Status |
| --- | --- | --- | --- |
| [T019](tasks/T019-streamlit-library-app.md) | Rewrite the Streamlit app over the library | T017 | planned |
| [T020](tasks/T020-drafting-mode.md) | Add the drafting mode | T019 | planned |
| [T021](tasks/T021-final-cleanup.md) | Remove leftovers and update documentation | T018, T020 | planned |

## After M3: candidate experiments

Not tasks yet. Each becomes a task only if the M3 baseline shows the problem it addresses; each is adopted only if it improves the gold-set metrics.

- LLM-written contextual prefixes for chunks (research §3).
- Parent/child (small-to-big) retrieval.
- Chunk size and overlap tuning; retrieval depth and RRF parameters.
- Multi-query rewriting for vague questions.
- Reference-list extraction with GROBID (open decision in STATUS).
- Upload-and-ingest from the UI; a local HTTP API.
