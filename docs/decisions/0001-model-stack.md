# 0001 — Model stack for parsing, retrieval, and generation

- Status: accepted (2026-11-14; the user delegated the choice of primary options to the assistant and set the constraints below)
- Research: [Модели для локального RAG](../research/reports/Модели%20для%20локального%20RAG.md), with notes in [research_notes](../research/research_notes/Модели%20для%20локального%20RAG/) (including `api_llm_cheapest.md` and `query_translation.md`)

## Context

The prototype used BAAI/bge-large-en-v1.5 + SciBERT embeddings, cross-encoder/nli-deberta-v3-base as reranker, PyMuPDF/pdfplumber heuristics for parsing, and `deepseek/deepseek-chat-v3-0324:free` on OpenRouter for generation. Both embedders and the reranker are English-only, the reranker is an entailment model rather than a relevance model, and the generation route no longer exists on OpenRouter (absent from its live model list on 2026-11-14).

Constraints set by the user: a general RAG over PDF and other text documents in several languages; one model in memory at a time; everything installed inside the project; the cheapest cloud model that passes the quality bar; only primary options installed. Hardware: RTX 3060 Laptop 6 GB VRAM, 16 GB RAM, Windows 11 without WSL.

## Decision

| Stage | Choice | Where it lives |
| --- | --- | --- |
| Parsing (PDF, DOCX, EPUB, HTML, …) | MinerU 4.2.2, tier `standard` (hybrid: torch layout/OCR models on CUDA + MinerU2.5-Pro 1.2B VLM via llama.cpp/Vulkan), run in-process with `mineru-kit parse` | `venv/`, models in `models/mineru/` |
| Query translation | The user's query is translated to English before retrieval. Cloud mode: the generation model below. Local mode: the local LLM below. | — |
| Embeddings | `microsoft/harrier-oss-v1-0.6b` (MIT), queries with `prompt_name="web_search_query"` | `models/harrier-oss-v1-0.6b/` |
| Lexical retrieval | BM25 via `bm25s`, combined with the embeddings (hybrid) | `venv/` |
| Reranker | `Qwen/Qwen3-Reranker-0.6B` (Apache-2.0) via sentence-transformers `CrossEncoder` | `models/Qwen3-Reranker-0.6B/` |
| Generation, cloud (default) | `deepseek/deepseek-v4.1-flash-1017` on OpenRouter, `reasoning.effort = "none"`, `provider = {zdr: true, data_collection: "deny", sort: "price"}` | `src/ragshelf/llm/deepseek_llm.py`; key in `.env` |
| Generation, local (offline) | Qwen3.5-9B IQ4_XS GGUF (`bartowski/Qwen_Qwen3.5-9B-GGUF`) served by llama.cpp `llama-server` b12373, CUDA 12.4 build | `models/gguf/`, `.tools/llama.cpp/` |
| Reference lists | Deferred; see Consequences | — |

Cloud model rationale: on 2026-11-14 it was the cheapest option meeting all criteria — Vectara hallucination rate 4.2% with 99.9% answer rate (leaderboard of 2026-10-22), Russian Text Arena rank #32, no announced retirement, and zero-data-retention endpoints on OpenRouter. Approximate cost: $0.70 per 1,000 queries of 8k input + 800 output tokens at the lowest listed price. Cheaper options failed a criterion (Gemma 4 26B A4B: 5.2% hallucination; Gemma 3 12B and Mistral Small: no Russian evidence; GPT-5.4 nano: shutdown 2027-04-01).

Query translation rationale: English queries score higher against English chunks (smoke test below), and the local 9B is stronger at translation than a separate 4B model (WMT24++ 72.6 vs 66.6, vendor figures) while already fitting in VRAM, so no second translation model is downloaded.

## Measurements on this PC (2026-11-14)

- MinerU `standard`: 3 pages of a scientific article in 7.5 s of inference (0.4 page/s) plus about 45 s one-time model load; headings, authors, sections and DOI extracted correctly.
- harrier-oss-v1-0.6b, bf16: 2.3 s load, 1,137 MiB VRAM; English, Russian and Slovak test queries each ranked the correct passage first (cosine 0.68 for English vs 0.57 for the same query in Russian).
- Qwen3-Reranker-0.6B, bf16: 2.0 s load, 1,144 MiB VRAM; 50 pairs of ~500 tokens in 1.58 s; clear separation of the relevant passage (+5…+7 vs −8…−11 logits). Scores are raw logits; apply a sigmoid for 0–1 values.
- Qwen3.5-9B IQ4_XS, all 33 layers on GPU: `llama-bench` pp8192 2,158 tok/s, tg128 58.4 tok/s. With `llama-server -c 16384` and default 4 slots, VRAM overflowed into shared memory (prefill 218 tok/s, decode 22.8 tok/s). With `--parallel 1 -ub 256 -b 1024` it stays on the GPU: an 11,568-token prompt took 7.8 s end to end (prefill 1,787 tok/s, decode 52.9 tok/s), VRAM 5.8 of 6.0 GiB, and the Russian answer was correct and cited the right chunk.

Local server command that fits:

```
.tools/llama.cpp/llama-server.exe -m models/gguf/Qwen_Qwen3.5-9B-IQ4_XS.gguf -ngl 99 -fa on -c 16384 --parallel 1 -ub 256 -b 1024 --host 127.0.0.1 --port 8081 --jinja
```

Disable thinking per request with `"chat_template_kwargs": {"enable_thinking": false}`. Stop the server before loading the embedder or reranker.

## Consequences

- Every document must be re-parsed and re-embedded; the old `chunks.json`/`embeddings.npy` in `data/library/` are incompatible.
- `MINERU_HOME` and `HF_HOME` must point inside the project (see `.env.example`); otherwise MinerU and Hugging Face write to the user profile. MinerU telemetry is disabled with `MINERU_TELEMETRY_DISABLED=1`.
- MinerU's server mode (`mineru parse`, `mineru server`) refuses to start because the project tree grants "Authenticated Users" modify rights and MinerU requires a private credential directory. In-process `mineru-kit parse` works and is the supported path here. Never pass `--remote`: it uploads documents to mineru.net.
- `pymupdf` (still used by the current loader) pulls plain `onnxruntime`, which overlaps with MinerU's `onnxruntime-directml`. Until the loader is replaced, confirm that `onnxruntime.get_available_providers()` lists `DmlExecutionProvider`.
- GROBID is not installed. Its documentation states that native Windows is not supported and recommends Docker; Docker Desktop on Windows 11 Home requires WSL2, which needs administrator rights, a reboot, and a system-wide install outside the project. Until the user decides on that, reference lists are to be parsed from the reference block that MinerU extracts.
- The cloud model needs an OpenRouter API key in `DEEPSEEK_API_KEY` (the variable name is kept from the prototype). Requests with this configuration have not been sent yet.
- Not yet verified: retrieval quality on a labelled Russian/Slovak → English query set, the translation step, and the cloud model on the project's own documents. Revisit this decision after that evaluation.
