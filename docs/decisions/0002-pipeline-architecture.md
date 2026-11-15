# 0002 — Pipeline architecture: storage, identity, chunking, layering

- Status: accepted (2026-11-16, by the user; proposed 2026-11-15)
- Implements: [requirements](../requirements.md) R1–R8 with the models in [ADR 0001](0001-model-stack.md)
- Research: [Production RAG architecture](../research/reports/Production%20RAG%20architecture.md)

## Context

The prototype (see "Prototype review" below) stores each document as `chunks.json` + `embeddings.npy`, builds an in-memory FAISS index on every start, numbers documents and chunks by position, splits text with PDF heuristics, clusters chunks with HDBSCAN, and generates without citations or abstention. ADR 0001 fixes the models but not how documents, chunks, and indexes are stored, identified, versioned, or evaluated.

## Decision

### Layering

`src/ragshelf/` is a library with one module per stage behind a small interface: `parse`, `documents` (model and metadata), `chunking`, `embed`, `index` (dense + lexical), `retrieve` (fusion, rerank), `context`, `generate`, `llm` (cloud and local clients), `eval`, `trace`, `config`, `models` (load/unload lifecycle). A `ragshelf` console script exposes `ingest`, `search`, `ask`, and `eval`. The Streamlit app calls the same library functions and holds no pipeline logic. Nothing loads a model at import time.

### Configuration

One typed configuration (pydantic-settings) read from `ragshelf.toml` at the repository root, overridable by environment variables; secrets only in `.env`. The OpenRouter key is read from `OPENROUTER_API_KEY` (renamed from the prototype's `DEEPSEEK_API_KEY`). The hash of the effective configuration is written into the index manifest and every query trace.

### Document identity and incremental ingestion

- Source documents live as plain files anywhere under `data/library/` (subfolders allowed). An optional sidecar `<file name>.metadata.json` overrides extracted metadata (R6). `ragshelf ingest` scans this folder; the prototype's `data/inbox/<N>/` and `data/library/article_<N>/` layouts are retired.
- `doc_id`: the document's path relative to `data/library/`, with forward slashes. `content_hash`: sha256 of the file bytes. A moved or renamed file is a new document; the parse cache still avoids re-parsing it.
- Unchanged hash → skip; changed → delete the document's chunks and re-ingest; missing file → delete its chunks.
- Parser output is cached under `data/cache/parse/<content_hash>/<parser-version-and-settings>/`, so changing the chunker or embedder never re-runs MinerU.
- Chunk ID: `<doc_id>#<ordinal>-<first 8 hex of sha256(text)>`.

### Storage

- Dense index: LanceDB, embedded, one table holding chunk ID, text, embedded text, vector, and metadata (doc_id, title, authors, year, DOI, heading path, page span, language).
- Lexical index: `bm25s` (ADR 0001) over the same chunk IDs and the same embedded text, saved next to the table.
- Both live under `data/index/<index-id>/` with `manifest.json` (embedder ID and revision, dimension, query prompt name, chunker version and parameters, parser version, BM25 tokenizer, configuration hash). Any change to these creates a new index ID; `data/index/current` names the active one. Vectors from different embedders are never mixed.
- Rejected: FAISS files (no metadata, deletion, or versioning; the prototype already had to build a store around them); Qdrant local mode (positioned for development use); sqlite-vec (pre-1.0). sqlite-vec + FTS5 is the fallback if LanceDB fails on this machine.

### Chunking

- Split MinerU Markdown on headings, then recursively on paragraphs and sentences, target 512 tokens and maximum 800 measured with the harrier tokenizer, overlap 0–15% (tuned with the eval). Tables, equations, code blocks, and figure captions stay whole; sections under ~100 tokens merge into a neighbour.
- The heading path (`Title > 3 Methods > 3.2 Data`) is prepended to the embedded and BM25-indexed text and stored separately for display.
- The reference list is stored per document and is not chunked into the index.
- No clustering stage. LLM-written chunk prefixes and parent/child (small-to-big) retrieval are experiments after the evaluation baseline, adopted only if they improve the gold-set metrics.

### Retrieval and generation

- The query is translated to English (ADR 0001); both forms are kept. Dense (harrier, `web_search_query` prompt) and BM25 each return the top 100; fused with RRF (k = 60); the top 50 fused are reranked by Qwen3-Reranker; the top N by reranker score (default 8) go to context. Raw scores from different stages are never added together.
- Context assembly deduplicates, merges adjacent chunks of one document, enforces a token budget, orders by document and position, and labels each chunk `[S1]…[Sn]` inside delimiters that mark it as untrusted data.
- The answer cites labels; citations not present in the context are removed and reported. The system abstains when the best reranker score is below a threshold set from the eval or when the model reports insufficient evidence. The answer is written in the language of the original query.
- The generation path has no tools. The UI does not render remote images or links from answers.

### Evaluation and tracing

- Gold set in `data/eval/` (not tracked: it quotes copyrighted documents). Labels are documents with page or section spans, not chunk IDs. Each query exists in ru, sk, and en; 10–20% are unanswerable.
- Retrieval metrics per stage: recall@50 before reranking, recall@5/10, MRR, nDCG@10 after. Answer metrics: faithfulness, citation precision/recall, abstention accuracy, judged by a model different from the generator and calibrated on human-graded items.
- Every `search`/`ask` call appends one JSONL record to `data/traces/` with the fields listed in the research report §5.

### Models in GPU memory

A lifecycle manager loads one model at a time and frees VRAM after use. Ingestion runs stage by stage over the whole batch (parse all, then embed all). The local-mode swap strategy (llama-server for translation and generation vs. embedder and reranker) is measured in T013 and recorded here before it is fixed.

## Prototype review

What changes and why, by module (state of commit `e4af34f`):

| Module | Problem | Action |
| --- | --- | --- |
| `scripts/process_sources.py` | Calls `split_references(raw_text)` but the function requires a second argument, so ingestion raises `TypeError`; numbers documents `article_N` by position; re-ingests the whole inbox on every run; `source` points to `references.txt`; runs on import. | Deleted (T001): it does not run and imports the clustering modules. Replaced by `ragshelf ingest` (T009). |
| `loaders/universal_loader.py` | PDF-only heuristics (columns, regex reference splitting) superseded by MinerU; pulls `pymupdf`, which conflicts with `onnxruntime-directml` (ADR 0001). | Replaced by `parse` and `documents` (T005–T006); deleted in T009 with `pymupdf` and `pdfplumber`. |
| `processing/chunker.py` | Drops every chunk `langdetect` does not classify as English, which contradicts R2; English-article-specific regex filters; `tiktoken` tokens instead of the embedder's tokenizer. | Replaced by `chunking` (T007); deleted in T009 with `langdetect` and `tiktoken`. |
| `processing/cluster_hdbscan.py`, `processing/chunk_clusterization.py` | Two overlapping clustering implementations; clustering is not a recognized way to form retrieval units; loads extra models. | Deleted (T001) with `hdbscan`. |
| `processing/token_counter.py` | Third copy of token counting. | Deleted (T001). |
| `embeddings/*` | English-only BGE + SciBERT concatenation. | Replaced by `embed` (T008); deleted in T009. |
| `store/dynamic_vector_store.py` | In-memory FAISS rebuilt each run; loads both embedders on every query; `KMP_DUPLICATE_LIB_OK` workaround; no persistence or deletion. | Replaced by `index` (T008); deleted in T009 with `faiss-cpu`. |
| `retrieval/reranker.py` | NLI entailment model used as a reranker; LLM reranking parses free text. | Replaced by Qwen3-Reranker (T013), deleted. |
| `llm/deepseek_llm.py` | No timeout or retries; HTTP errors are printed and returned as answer text; no local client. | Replaced by `llm` clients (T004). |
| `generation/rag_chain.py` | Concatenates chunks without labels; no citations, abstention, or injection boundary; a new client per call. | Replaced by `context` + `generate` (T016–T017), deleted. |
| `app/streamlit_app.py` | Indexes one uploaded PDF in memory, writes `temp.pdf` to the working directory, top-3 dense only, no citations. | Rewritten over the library (T019). |
| `legacy/`, `scripts/chunk_experiment.py` | Experiments not on any path. | Deleted (T001). |

## Consequences

- New dependencies: `lancedb`, `pydantic-settings`; `pytest` for development. `lancedb` 0.41.0 and `pylance` publish `cp310-abi3-win_amd64` wheels, so they are expected to install on Python 3.14; installation is verified in T008.
- Removed dependencies: `faiss-cpu`, `hdbscan`, `langdetect`, `pdfplumber`, `pymupdf`, `tiktoken`, and `scikit-learn` if nothing else needs it. Removing `faiss-cpu` and `hdbscan` also removes the reason Python 3.15 is blocked (README); that is rechecked after removal, not assumed.
- Between T009 and T019 the Streamlit app does not work; the CLI is the interface.
- Existing outputs in `data/library/article_*` are incompatible (ADR 0001) and are migrated in T005 after the user confirms it.
