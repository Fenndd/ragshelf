# Production RAG architecture, scaled to a single-user local library

- Date: 2026-11-15
- Prepared by: a delegated research subagent (tier 3, preset `opus-high`; actual model and effort not reported by the tool), read-only, web sources. Reviewed and condensed by the main session.
- Scope: how a production-quality RAG is built and evaluated, given the model stack already fixed in [ADR 0001](../../decisions/0001-model-stack.md). Model choice is out of scope.
- Status: research material, not a decision. Decisions drawn from it are in the accepted [ADR 0002](../../decisions/0002-pipeline-architecture.md).

Most sources are vendor or practitioner write-ups. Contested or unverified claims are marked.

## 1. Reference architecture

Ingestion: parse (MinerU → Markdown) → normalize (Unicode NFC, hyphenation, repeated headers/footers removed, page numbers kept as metadata) → structure-aware chunking (§3) → metadata (doc_id, source, title, heading path, page span, language, parser/chunker version) → embed passages (no query prompt) → write the vector index and a BM25 index over the same chunk IDs as one versioned unit.

Query: translate/rewrite to English, keeping the original → dense top ~50–150 and BM25 top ~50–150 in parallel → Reciprocal Rank Fusion (k≈60; needs no score calibration) → rerank, keep top ~5–20 → assemble context (dedupe, merge adjacent chunks, token budget, order by document and position, citation label per chunk) → grounded generation that cites chunk IDs → abstain when evidence is insufficient; verify that every cited ID was in the context.

Measured effects (Anthropic): top-20 retrieval failure 5.7% with embeddings only, 2.9% with contextual embeddings + BM25, 1.9% with reranking (top 150 reranked to 20). The metric checks retrieval of the golden chunk, not answer quality. Google's "Sufficient Context" paper finds models often answer wrongly rather than abstain when context is insufficient; a sufficiency signal improved the share of correct answers among answered ones by 2–10%.

- https://www.anthropic.com/news/contextual-retrieval
- https://arxiv.org/abs/2411.06037
- https://docs.lancedb.com/reranking/rrf

## 2. Data and index management

- Stable `doc_id` plus `content_hash` (sha256 of file bytes): unchanged → skip; changed → delete the document's chunks and re-ingest; file gone → delete its chunks. Chunk IDs are deterministic (`doc_id:ordinal:hash(text)`), never list positions.
- Cache parser output keyed by (content_hash, parser version and settings). At 0.4 page/s (ADR 0001) parsing dominates cost, so this cache is the most valuable part of incremental indexing.
- Each index carries a manifest: embedder ID and revision, dimension, query prompt name, chunker version and parameters, normalization version, BM25 tokenizer. A change creates a new index directory; build beside the old one, evaluate, then switch. Never mix vectors from different embedders. LangChain's RecordManager is a reference design.
- Vector store: LanceDB (embedded, in-process, no server; vectors + text + metadata on disk; upsert and delete by key; table versions with checkout/restore). Caveats: deletes and old versions use disk until compaction; SDK method names change between versions. Alternatives: sqlite-vec + FTS5 (one transactional file, pre-1.0; brute force is fine at this scale), Qdrant local mode (positioned for development and testing), FAISS files (no metadata, deletion, or versioning). Judgment call; no head-to-head benchmark found.

- https://python.langchain.com/docs/how_to/indexing
- https://docs.lancedb.com/tables/versioning
- https://github.com/asg017/sqlite-vec/releases

## 3. Chunking structured Markdown

- Split on headings, then recursively on paragraphs and sentences to roughly 300–800 tokens (~512 is a common default; Anthropic used ~800). Keep tables, code blocks, equations, and captions whole; merge tiny sections into neighbours. Overlap 0–15%. Chroma's evaluation finds well-parameterized recursive splitters competitive and chunking choices change recall noticeably. (Size and overlap figures partly rest on secondary blogs.)
- Semantic (embedding-boundary) chunking: contested; one benchmark, cited secondhand, shows higher recall but lower end-to-end accuracy.
- Prepend the heading path ("Title > 3 Methods > 3.2 Data") to the embedded and BM25-indexed text: a cheap contextual header. LLM-written per-chunk prefixes (Anthropic) cost an extra GPU pass with the local 9B model; worth measuring, not assuming.
- Small-to-big (retrieve child chunks, return the parent section within budget): LlamaIndex AutoMergingRetriever is the reference.
- Clustering (HDBSCAN or otherwise) is not a recognized way to form retrieval units. It appears only as an extra layer (RAPTOR summary trees with GMM; research query routers).

- https://research.trychroma.com/evaluating-chunking
- https://developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/
- https://arxiv.org/abs/2401.18059

## 4. Evaluation

- Gold set: start with 50–100 hand-written queries, grow to ~200 (practitioner rule of thumb). Per item: the same intent in ru, sk, and en (tests translation); relevant documents with page or section spans, not chunk IDs, so labels survive re-chunking; a short reference answer; 10–20% unanswerable items.
- Retrieval metrics (deterministic, no judge): recall@50 before reranking (the ceiling for the reranker), recall@5/10, MRR, nDCG@10 after; per stage (dense, BM25, fused, reranked).
- Answer metrics: faithfulness (share of claims supported by context, RAGAS style), citation precision/recall (ALCE), answer relevance, abstention accuracy.
- LLM-as-judge has position, verbosity, and self-preference biases. Use a judge different from the generator, calibrate on 30–50 human-graded items (target ~90% agreement).
- Regression gating: pin dataset, config, models, prompts per run; gate hard on retrieval metrics; treat judge metrics as trends. With ~100 queries, differences of a few points are noise (statistical caveat, not sourced).

- https://arxiv.org/abs/2104.08663
- https://arxiv.org/abs/2311.09476 and https://docs.ragas.io
- https://arxiv.org/abs/2306.05685

## 5. Engineering

- One typed configuration loaded from file, environment, and `.env` (secrets only in `.env`); its hash goes into the index manifest and every trace.
- Library with narrow interfaces (parser, chunker, embedder, reranker, LLM, store, pipeline); CLI on top (`ingest`, `query`, `eval`); UI holds no logic.
- Tests: unit tests with fakes (hash embedder, lexical reranker, scripted LLM); golden-file tests for normalizer and chunker; fusion and abstention logic; one slow smoke test with real models on 2–3 permitted fixtures.
- Tracing: one local JSONL record per query (original and translated query, IDs and scores per stage, context IDs, prompt version, model and route, per-stage latency, answer, cited IDs, abstained flag). OpenTelemetry GenAI conventions are still in development; Arize Phoenix is an optional local viewer.
- VRAM: explicit model lifecycle (load, use, free; nothing loaded at import); ingestion stage by stage. Local query mode conflicts: the 9B needs 5.8 GB while embedder and reranker need ~1.1 GB each; swap cost with `llama-server` restarts is unmeasured.
- Prompt injection: document text is untrusted (OWASP LLM01, indirect injection). Delimit chunks and instruct the model to treat them as data; no tools on the generation path; do not render remote images or auto-links from answers; validate citations against context IDs.
- Privacy: cloud mode sends chunks to OpenRouter (ZDR configured per ADR 0001); keep traces and indexes local and out of Git; offline mode is first-class.

- https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- https://docs.arize.com/phoenix/

## 6. Prototype anti-patterns

Monolithic `chunks.json`/`embeddings.npy` with positional IDs and full rebuilds; mixed or unrecorded embedders; mismatched query/passage encoding; splitting that ignores headings and breaks tables; weighted sums of raw cosine and BM25 scores or absolute thresholds carried between models; an NLI model as reranker; top-k stuffed into the prompt without dedupe or budget; unverified citations; prompts that allow answering from the model's own knowledge; global models and hardcoded paths, keys, or model names; silent fallbacks and swallowed exceptions; `print` debugging and tuning by eye without a gold set.

## Open points

LanceDB vs sqlite-vec is a judgment call; chunk size/overlap figures are partly secondary; gold-set size is a rule of thumb; local-mode VRAM swapping needs measurement; the value of LLM-written chunk prefixes is unmeasured.
