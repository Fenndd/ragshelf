# Multilingual rerankers for the local RAG system (state as of November 2026)

Scope: replacing `cross-encoder/nli-deberta-v3-base`, which is an NLI/entailment model and not a relevance reranker. Target: RTX 3060 Laptop 6 GB (Ampere, sm_86), 16 GB RAM, Windows 11, Python 3.14.10, torch 2.14.1+cu130. Mostly English scientific documents, plus Russian and Slovak; Russian queries; cross-lingual reranking required; public open-source repository.

Research date: 2026-11-14. Weights were not downloaded and nothing was run. All latency and VRAM figures for the target laptop are estimates, labelled as such in the Inferences sections. Policy check: this was assigned as tier 3 under `docs/engineering/AI_ORCHESTRATION.md`. That fits: sources contradict each other and options must be compared. No tier-4 condition applies because the work is read-only and nothing is irreversible.

## 1. Which rerankers lead in late 2026, and when were they released?

### Takeaway
No new multilingual text reranker in 2026 has clearly replaced the 2025 generation for local use. The leading open models are still the Qwen3-Reranker family (June 2025, Apache-2.0), jina-reranker-v3 (Sep/Oct 2025) and jina-reranker-v3.5 (Jul/Aug 2026), but both Jina models are CC BY-NC. mxbai-rerank-v2 (June 2025, Apache-2.0) and bge-reranker-v2-m3 (2024, Apache-2.0) are the established baselines. The 2026 releases are mostly multimodal (Qwen3-VL-Reranker in Jan 2026, NVIDIA Nemotron-3.5-Rerank-8B in Oct 2026) or closed APIs (Cohere Rerank 5, Voyage rerank-3).

### Cited Findings
- **Qwen3-Reranker 0.6B / 4B / 8B.** The paper arXiv 2506.05176 was published 2025-06-05. The models are Apache-2.0, have a 32k context, cover 100+ languages, accept instructions, and score with yes/no logits from a causal LM. — [HF Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B); [Qwen blog](https://qwenlm.github.io/blog/qwen3-embedding); [arXiv 2506.05176](https://arxiv.org/pdf/2506.05176v3)
- **jina-reranker-v3.** A 0.6B listwise reranker built on Qwen3-0.6B ("last but not late interaction"). It handles up to 64 documents at once in a 131K-token context. The paper arXiv 2509.25085 dates from 2025-09-29 and the blog announcement from 2025-10-03. License: CC BY-NC 4.0. — [HF card](https://huggingface.co/jinaai/jina-reranker-v3); [Jina blog](https://jina.ai/news/jina-reranker-v3-0-6b-listwise-reranker-for-sota-multilingual-retrieval/); [arXiv](https://arxiv.org/html/2509.25085v4)
- **jina-reranker-v3.5.** 0.6B, fine-tuned from Qwen3-0.6B with hybrid attention, 131K context, CC BY-NC 4.0 (commercial use only by contacting Jina). The paper arXiv 2607.18152 was published 2026-07-20, and a roundup gives the release as August 2026. The card says it is 1.22x to 1.56x faster than v3 on an A100 with FlashAttention-2. — [HF card](https://huggingface.co/jinaai/jina-reranker-v3.5); [futureagi roundup (updated 2026-10-29)](https://futureagi.com/blog/best-rerankers-for-rag-2026/)
- **mxbai-rerank-base-v2 (0.5B) and large-v2 ("ProRank-1.5B"; the HF safetensors widget shows 2B).** Apache-2.0, Qwen2 architecture, 100+ languages. The paper arXiv 2506.03487 is dated 2025-06-04. — [HF mxbai-rerank-large-v2](https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v2)
- **bge-reranker-v2-m3.** 568M parameters, based on bge-m3 (XLM-R), Apache-2.0. The related papers are from Dec 2023 and Feb 2024, so this is older. A sibling LLM-based model, bge-reranker-v2-gemma (2.5B), and bge-reranker-v2-minicpm-layerwise also exist. — [HF card](https://huggingface.co/BAAI/bge-reranker-v2-m3); [recal.so (2026-08-01)](https://www.recal.so/blog/best-local-reranker-models-2026)
- **gte-multilingual-reranker-base.** About 306M parameters, Apache-2.0, 8192 tokens, 70+ languages, requires `trust_remote_code`. The paper arXiv 2407.19669 is from 2024-07 (older). — [HF card](https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base)
- **NVIDIA llama-nemotron-rerank-1b-v2.** 1B, fine-tuned from Llama-3.2-1B, 8192 tokens, evaluated on 26 languages including Russian and Czech; Slovak is not listed. Licensed under OpenMDW-1.1 plus the Llama 3.2 Community License ("Built with Llama"). Only Linux is listed as a supported OS, and it requires `trust_remote_code`. The card gives no release date. — [HF card](https://huggingface.co/nvidia/llama-nemotron-rerank-1b-v2)
- **NVIDIA Nemotron-3.5-Rerank-8B-BF16.** 8.38B, multimodal (text plus page images), 32,768 context, OpenMDW-1.1, released 2026-10-20. Tested on A100, H100 and GB200 under Linux only. Supported via sentence-transformers 6.1 `CrossEncoder` and transformers 5.20. — [HF card](https://huggingface.co/nvidia/Nemotron-3.5-Rerank-8B-BF16); [reranker.uk release watch](https://github.com/sheephess9527/reranker.uk/issues/47)
- **Qwen3-VL-Reranker 2B / 8B.** Multimodal (text, image, video), 30+ languages. arXiv 2601.04720 was submitted 2026-01-08. Aggregators report Apache-2.0; I did not verify this on the HF card. — [arXiv 2601.04720](https://arxiv.org/abs/2601.04720); [DataLearner](https://www.datalearner.com/en/ai-models/pretrained-models/qwen3-vl-reranker-8b)
- **Closed APIs in 2026, not open weights:**
  - Cohere Rerank 5 Pro/Fast, released 2026-10-21. Vendor figure: 82.2 on BRIGHT.
  - Voyage rerank-3, released 2026-09-30.
  - Zerank 2 led the Agentset Elo leaderboard (1638) in Feb 2026.
  - Sources: [futureagi](https://futureagi.com/blog/best-rerankers-for-rag-2026/); [reranker.uk](https://github.com/sheephess9527/reranker.uk/issues/47)
- **Other 2026 Hugging Face items:** castorini/gaggle-reranker-run3-20261002 (3.22B pointwise research model) and caveman-so/trim-1. The tracker judged trim-1 to be a context compressor, not a reranker. — [castorini HF](https://huggingface.co/castorini/gaggle-reranker-run3-20261002); [reranker.uk](https://github.com/sheephess9527/reranker.uk/issues/47)
- **ColBERTv2** (MIT) is still mentioned as the late-interaction option for long documents. — [futureagi](https://futureagi.com/blog/best-rerankers-for-rag-2026/); [dev.to](https://dev.to/gabrielanhaia/reranker-selection-cross-encoder-vs-llm-as-reranker-vs-colbert-which-earns-its-latency-2h7o)
- **2026 practitioner roundups:**
  - recal.so (2026-08-01) recommends bge-reranker-v2-m3 as the default for local RAG, Qwen3-Reranker-4B/8B for maximum accuracy, and warns that jina-v2 is non-commercial. — [recal.so](https://www.recal.so/blog/best-local-reranker-models-2026)
  - SiliconFlow lists Qwen3-Reranker first, but SiliconFlow hosts Qwen3, so the ranking is vendor-biased. — [SiliconFlow](https://www.siliconflow.com/articles/best-reranker-for-cross-lingual-search)

### Inferences
- For a text-only scientific corpus, the 2026 multimodal releases (Qwen3-VL-Reranker, Nemotron-3.5-Rerank-8B) add size without a documented text-quality gain. The text-only candidates therefore remain the 2025 models.
- The current model, nli-deberta-v3-base, is trained for entailment, not query–passage relevance. It is also English-only, so it is the wrong tool for Russian queries.

### Gaps
- I found no Qwen3.5-based text reranker; the search returned nothing.
- Exact Hugging Face publication dates for the Qwen3-Reranker, mxbai v2 and bge models are not on the cards. Paper dates were used instead.
- I did not verify the exact terms of OpenMDW-1.1 beyond its name.

## 2. How do they score on BEIR, MTEB, multilingual and cross-lingual benchmarks, and on scientific data?

### Takeaway
Rankings depend heavily on the evaluation protocol. Two vendor tables contradict each other on bge-reranker-v2-m3 versus Qwen3-Reranker-0.6B. Under Qwen's protocol, Qwen3-Reranker-0.6B beats bge-reranker-v2-m3, gte and jina-v2 on MMTEB-R and MLDR. Under Jina's protocol, bge-reranker-v2-m3 is best or near-best on MIRACL. Qwen3-Reranker-4B is the strongest open Apache model in every table. On the cross-lingual MKQA set, most modern rerankers are within about 2.6 points of each other (65–68).

### Cited Findings
- **Qwen's own table.** Each model reranks the top-100 from Qwen3-Embedding-0.6B. Columns are MTEB-R / CMTEB-R / MMTEB-R / MLDR / MTEB-Code / FollowIR. — [HF Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)

  | Model | MTEB-R | CMTEB-R | MMTEB-R | MLDR | MTEB-Code | FollowIR |
  |---|---|---|---|---|---|---|
  | Qwen3-Embedding-0.6B (no reranker) | 61.82 | 71.02 | 64.64 | 50.26 | 75.41 | 5.09 |
  | jina-multilingual-reranker-v2-base | 58.22 | 63.37 | 63.73 | 39.66 | 58.98 | -0.68 |
  | gte-multilingual-reranker-base | 59.51 | 74.08 | 59.44 | 66.33 | 54.18 | -1.64 |
  | bge-reranker-v2-m3 | 57.03 | 72.16 | 58.36 | 59.51 | 41.38 | -0.01 |
  | Qwen3-Reranker-0.6B | 65.80 | 71.31 | 66.36 | 67.28 | 73.42 | 5.41 |
  | Qwen3-Reranker-4B | 69.76 | 75.94 | 72.74 | 69.97 | 81.20 | 14.84 |
  | Qwen3-Reranker-8B | 69.02 | 77.45 | 72.94 | 70.19 | 81.22 | 8.05 |

- **Jina's v3 table (nDCG@10).** Columns are BEIR / MIRACL / MKQA / CoIR. — [HF jina-reranker-v3](https://huggingface.co/jinaai/jina-reranker-v3)

  | Model | BEIR | MIRACL | MKQA | CoIR |
  |---|---|---|---|---|
  | jina-reranker-v3 | 61.94 | 66.83 | 67.92 | 70.64 |
  | bge-reranker-v2-m3 | 56.51 | **69.32** | 67.88 | 36.28 |
  | mxbai-rerank-large-v2 | 61.44 | 57.94 | 67.06 | 70.87 |
  | mxbai-rerank-base-v2 | 58.40 | 55.32 | 64.24 | 65.71 |
  | Qwen3-Reranker-0.6B | 56.28 | 57.70 | 65.34 | 65.18 |
  | Qwen3-Reranker-4B | 61.16 | 67.52 | 67.52 | 73.91 |

- **Jina's v3.5 table.** Columns are BEIR / MIRACL / RTEB / Struct-IR. It reports different numbers for the same models, so the protocol differs. — [HF jina-reranker-v3.5](https://huggingface.co/jinaai/jina-reranker-v3.5)

  | Model | BEIR | MIRACL | RTEB | Struct-IR |
  |---|---|---|---|---|
  | jina-v3.5 | 63.20 | 74.11 | 70.95 | 48.3 |
  | jina-v3 | 62.10 | 72.20 | 68.01 | 38.7 |
  | Qwen3-Reranker-4B | 62.28 | **76.56** | **77.68** | **55.6** |
  | Qwen3-Reranker-0.6B | 56.94 | 67.12 | 68.41 | 41.9 |
  | mxbai-large-v2 | 62.45 | 69.65 | 70.81 | 43.0 |
  | mxbai-base-v2 | 59.58 | 64.90 | 61.44 | 30.4 |

- **Conflicts between the tables:**
  - Qwen3-Reranker-0.6B on MIRACL: 57.70 in the v3 table versus 67.12 in the v3.5 table.
  - jina-v3 on BEIR: 61.94 in the v3 card versus 61.85 in a later arXiv version. — [Jina blog](https://jina.ai/news/jina-reranker-v3-0-6b-listwise-reranker-for-sota-multilingual-retrieval/)
  - bge-reranker-v2-m3 on multilingual sets: 58.36 MMTEB-R in Qwen's table, but the best MIRACL score (69.32) in Jina's v3 table.
  - Sources: [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B); [Jina card](https://huggingface.co/jinaai/jina-reranker-v3)
- **mxbai's own table.** BEIR / Multilingual / Chinese / Code / latency on an A100: large-v2 57.49 / 29.79 / 84.16 / 32.05 / 0.89 s; base-v2 55.57 / 28.56 / 83.70 / 31.73 / 0.67 s. These use mxbai's own metric definitions, so they are not comparable with the tables above. — [HF mxbai-rerank-large-v2](https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v2)
- **Cross-lingual results.** NVIDIA llama-nemotron-rerank-1b-v2, Recall@5 with the reranker versus the embedder alone:
  - MLQA (cross-lingual): 86.83 vs 79.86
  - MIRACL: 65.80 vs 60.75
  - MLDR: 70.69 vs 59.55; BM25 scores 71.39 on MLDR, higher than the pipeline
  - Source: [HF card](https://huggingface.co/nvidia/llama-nemotron-rerank-1b-v2)
- **Russian.** The RusBEIR paper (arXiv 2504.12879, 2025) found that BGE-M3 plus bge-reranker-v2-m3 was the best combination on 17 Russian IR datasets. BM25 plus the BGE reranker was competitive for full-document retrieval. Qwen3-Reranker was not evaluated. — [arXiv 2504.12879](https://arxiv.org/pdf/2504.12879); [rusBEIR-lite](https://sergeyzh-rusbeir-lite.static.hf.space/index.html)
- **Independent 2026 test (aimultiple).** English Amazon reviews, multilingual-e5-base retrieving the top-100, H100. Hit@1 results:
  - e5 alone: 62.67%
  - nemotron-rerank-1b: 83.00% (243 ms)
  - gte-modernbert-base: 83.00%
  - jina-reranker-v3: 81.33% (188 ms)
  - Qwen3-Reranker-4B: 77.67% (over 1 s)
  - mxbai-rerank-xsmall: 64.67%
  - Results for bge-reranker-v2-m3 and Qwen3-Reranker-0.6B were not shown in the text.
  - Source: [aimultiple (updated 2026)](https://aimultiple.com/rerankers)

### Inferences
- The two tables most relevant to this project agree on Qwen3-Reranker-4B. They are MMTEB-R (Qwen's protocol) and MKQA/MIRACL (Jina's v3.5 protocol), and both rank Qwen3-Reranker-4B at or near the top among Apache-licensed models.
- For the 0.6B class, Qwen3-Reranker-0.6B and bge-reranker-v2-m3 trade places depending on the protocol. A local A/B test on the project's own Russian-query to English-passage set is the only way to decide between them.
- MKQA is commonly described as questions in 26 languages over English-centric answers, which makes it the closest public proxy for Russian queries against English passages. That description is from background knowledge and was not verified in this session.

### Gaps
- I found no published Russian-query to English-passage reranking benchmark that compares Qwen3-Reranker, bge, jina and mxbai.
- I found no Slovak-specific reranking results.
- I found no scientific-domain results (SciFact/SCIDOCS/TREC-COVID per model). BEIR averages include those sets, but the per-dataset values were not extracted.

## 3. Practical properties: size, VRAM, latency on a 6 GB laptop GPU, max input length, and pointwise vs listwise vs LLM-based

### Takeaway
Every 0.5–1.5B reranker fits comfortably in 6 GB at fp16/bf16. Qwen3-Reranker-4B does not fit in bf16 (about 8 GB of weights) and would need 4–8-bit quantization (GGUF or bitsandbytes). No measured latencies exist for an RTX 3060 Laptop. Measurements on other GPUs suggest a 0.6B reranker scores 100 chunks of 512 tokens in roughly 0.1–2 s, depending on the model and setup.

### Cited Findings
- **Parameter counts** (recal.so): ms-marco-MiniLM-L6 22.7M; bge-reranker-base 278M (MIT); mxbai-base-v2 494M; bge-reranker-v2-m3 568M; Qwen3-Reranker-0.6B 596M; bge-reranker-v2-gemma 2.5B; Qwen3-4B 4.0B; Qwen3-8B 8.2B. The article says quantization is close to mandatory for 4B/8B on a laptop. — [recal.so](https://www.recal.so/blog/best-local-reranker-models-2026)
- **Maximum input length:**
  - Qwen3-Reranker: 32k — [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
  - jina v3 / v3.5: 131K across up to 64 documents — [jina v3 card](https://huggingface.co/jinaai/jina-reranker-v3)
  - gte-multilingual-reranker: 8192 — [gte card](https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base)
  - nemotron-rerank-1b: 8192 — [nemotron card](https://huggingface.co/nvidia/llama-nemotron-rerank-1b-v2)
  - bge-reranker-v2-m3: the example uses `max_length=512` — [bge card](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- **Latency measurements on other GPUs:**
  - bge-reranker-v2-m3 fp16: about 60–90 ms per query for 50 candidates on an A10G; 700–1500 ms on a Xeon CPU — [dev.to](https://dev.to/gabrielanhaia/reranker-selection-cross-encoder-vs-llm-as-reranker-vs-colbert-which-earns-its-latency-2h7o)
  - bge-reranker-v2-m3: about 80–120 ms for 100 candidates on an RTX 4060 Ti, per a vendor tutorial with no methodology — [gigagpu](https://gigagpu.com/?p=33008)
  - Qwen3-Reranker-0.6B: 1.73 s average for 100 documents on an RTX 4090 with FA2, per a CSDN post of weak methodology — [CSDN](https://aicoding.csdn.net/6a771e6d10ee7a33f2987dce.html)
  - Qwen3-Reranker-4B: over 1 s per query of 100 candidates on an H100 — [aimultiple](https://aimultiple.com/rerankers)
  - jina-v3: 188 ms on an H100 — [aimultiple](https://aimultiple.com/rerankers)
- **Scoring modes:**
  - Qwen3-Reranker is pointwise but LLM-based: it reads the logits of "yes" and "no" on the last token. — [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
  - jina-v3 / v3.5 are listwise: all candidates go in one context window. — [jina v3 card](https://huggingface.co/jinaai/jina-reranker-v3)
  - bge-reranker-v2-m3 and gte are classic encoder cross-encoders.

### Inferences (estimates, not measured)
- **VRAM.** bf16 weights take about 2 bytes per parameter:
  - Qwen3-0.6B ≈ 1.2 GB, bge-v2-m3 ≈ 1.1 GB, mxbai-large-v2 ≈ 3–4 GB. All fit in 6 GB with room for batch activations.
  - Qwen3-4B ≈ 8 GB in bf16, which does not fit. A Q4_K_M GGUF is about 2.5 GB, and 4-bit bitsandbytes is about 2.5–3 GB.
  - Ampere (sm_86) supports bf16.
- **Compute cost of the target workload.** 100 chunks × 512 tokens is about 51k tokens per query. At roughly 2 FLOPs per parameter per token, a 0.6B model needs about 6×10^13 FLOPs.
- **Estimated latency on the RTX 3060 Laptop** (about 40 TFLOPS fp16 tensor peak, at realistic utilization):
  - 0.6B class: about 1.5–5 s for 100 chunks, or 0.5–1.5 s for 30.
  - bge-v2-m3: probably somewhat faster than this, since about 250M of its 568M parameters are embedding parameters that cost almost nothing per token.
  - Qwen3-4B (quantized): roughly 6–8 times slower, so about 10–40 s for 100 chunks. That is acceptable only for offline or batch use.
- **Windows.** flash-attention-2 is generally not available as a prebuilt wheel for Windows. Assume PyTorch SDPA instead, so the FA2-based speed figures will not carry over. This is background knowledge and was not verified in this session.

### Gaps
- No measured RTX 3060 Laptop (6 GB) latency exists for any candidate. Measure locally with fixed batch size, dtype and chunk length.
- I found no reliable VRAM-at-batch figures from any source.

## 4. Is a dedicated reranker still worth it, compared with a strong embedder alone or LLM-based reranking with a small local LLM?

### Takeaway
Yes, but only if the reranker is clearly stronger than the first-stage embedder. In Qwen's own table, older rerankers (bge-v2-m3, gte, jina-v2) score below the Qwen3-Embedding-0.6B baseline on MMTEB-R, so a weak reranker can make results worse. Strong rerankers add about 2–20 points depending on the setup. Prompting a general LLM listwise gains a few nDCG points over a cross-encoder, at 10–100 times the latency.

### Cited Findings
- **Qwen's table (MMTEB-R).** The embedder alone scores 64.64. Rerankers on top of it score: bge-v2-m3 58.36, gte 59.44, jina-v2 63.73 (all worse), Qwen3-0.6B 66.36 (+1.7), Qwen3-4B 72.74 (+8.1). On MLDR, the embedder scores 50.26 and Qwen3-0.6B 67.28 (+17). — [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
- **NVIDIA nemotron-rerank-1b.** Recall@5 gains over the embedder: +5 on MIRACL, +7 on MLQA (cross-lingual), +11 on MLDR. — [nemotron card](https://huggingface.co/nvidia/llama-nemotron-rerank-1b-v2)
- **aimultiple.** With a weak multilingual-e5-base retriever, rerankers raised Hit@1 from 62.67% to as much as 83%. — [aimultiple](https://aimultiple.com/rerankers)
- **dev.to, internal benchmark on an A10G:**

  | Setup | Recall@10 / nDCG@10 | p95 latency |
  |---|---|---|
  | No rerank | 0.71 / 0.58 | n/a |
  | bge-v2-m3 | 0.86 / 0.74 | 84 ms |
  | Claude Haiku 4.5 listwise | 0.91 / 0.81 | 1100 ms |
  | ColBERTv2 | 0.87 / 0.77 | 220 ms |

  The author's conclusion: an LLM reranker mainly buys about 5–7 nDCG points. — [dev.to](https://dev.to/gabrielanhaia/reranker-selection-cross-encoder-vs-llm-as-reranker-vs-colbert-which-earns-its-latency-2h7o)
- **mixedbread's July 2026 test (reported by futureagi).** GPT-5.6 rerankers at high reasoning effort took about 36–73 s per query, versus about 0.65 s for a dedicated listwise model. — [futureagi](https://futureagi.com/blog/best-rerankers-for-rag-2026/)
- **Pool recall.** A reranker cannot recover chunks that retrieval missed, so measure pool recall first. — [recal.so](https://www.recal.so/blog/best-local-reranker-models-2026)
- **Score thresholds.** Raw reranker scores are not comparable across models; thresholds must be calibrated for each reranker. — [dev.to](https://dev.to/gabrielanhaia/reranker-selection-cross-encoder-vs-llm-as-reranker-vs-colbert-which-earns-its-latency-2h7o)

### Inferences
- Qwen3-Reranker is already an LLM-based reranker: a Qwen3 LLM fine-tuned to output yes/no. That makes it the practical middle ground between a classic cross-encoder and prompting a general local LLM. A generic 1–4B chat LLM prompted listwise on a 6 GB GPU would almost certainly be slower than this, and probably less accurate. That comparison has not been measured.
- The remote-LLM reranking path can stay as an optional "high quality" mode. The evidence suggests a few points of gain at a large latency and cost penalty.

### Gaps
- I found no published head-to-head of a dedicated reranker against a small local LLM (1–4B, e.g. a Qwen3-4B chat model) prompted for listwise reranking.

## 5. Will they run with sentence-transformers / transformers on Python 3.14, torch 2.14 + CUDA 13.0, Windows? Are GGUF or ONNX versions available?

### Takeaway
sentence-transformers 6.2.0 (2026-10-21) officially supports Python 3.14. Qwen3-Reranker, bge-reranker-v2-m3 and mxbai-rerank-v2 load directly with `CrossEncoder`. The Jina, gte and NVIDIA models need `trust_remote_code`, and the NVIDIA cards list Linux only. Community GGUF builds exist for every Qwen3-Reranker size, but their conversion quality varies.

### Cited Findings
- **sentence-transformers v6.2.0** (2026-10-21): adds Python 3.14 support and `huggingface_hub` 2.x support. It states no torch minimum except PyTorch ≥2.9 for MPS. It also has ONNX external-weights fixes and an OpenVINO extra. — [release notes](https://github.com/huggingface/sentence-transformers/releases/tag/v6.2.0); [reranker.uk](https://github.com/sheephess9527/reranker.uk/issues/47)
- **Qwen3-Reranker:**
  - Supported via sentence-transformers `CrossEncoder` with `predict` and `rank`. The default output is logit differences; pass `activation_fn=torch.nn.Sigmoid()` to get 0–1 scores.
  - Instructions are passed through `prompts` and give +1–5%. Write instructions in English even for multilingual use.
  - Requires transformers ≥4.51. vLLM ≥0.8.5 is also supported (vLLM targets Linux).
  - Source: [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
- **bge-reranker-v2-m3:** sentence-transformers `CrossEncoder`, FlagEmbedding `FlagReranker(use_fp16=True)`, or transformers `AutoModelForSequenceClassification`. — [bge card](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- **mxbai-rerank-v2:** sentence-transformers `CrossEncoder`, the `mxbai-rerank` package, or transformers `AutoModelForCausalLM`. — [mxbai card](https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v2)
- **jina v3 / v3.5:** `AutoModel` with `trust_remote_code=True` and `model.rerank()`. GGUF and MLX versions exist; sentence-transformers is not mentioned. — [jina v3](https://huggingface.co/jinaai/jina-reranker-v3); [jina v3.5](https://huggingface.co/jinaai/jina-reranker-v3.5)
- **gte-multilingual-reranker-base:** `CrossEncoder` with `trust_remote_code=True`. ONNX is not mentioned. — [gte card](https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base)
- **NVIDIA rerankers:**
  - nemotron-rerank-1b: transformers ≥4.44 with `trust_remote_code`; Linux is the only listed OS. — [card](https://huggingface.co/nvidia/llama-nemotron-rerank-1b-v2)
  - Nemotron-3.5-8B: transformers 5.20 and sentence-transformers 6.1; Python 3.12 recommended; Linux only. — [card](https://huggingface.co/nvidia/Nemotron-3.5-Rerank-8B-BF16)
- **Qwen3-Reranker GGUF:**
  - Builds exist for every size, including ggml-org's Qwen3-Reranker-0.6B-Q8_0-GGUF and community 4B/8B quantizations.
  - Run with `llama-server --reranking` on the `/v1/rerank` endpoint.
  - Some conversions return near-zero or wrong scores, and older reports say a fix branch was required. Whether current mainline llama.cpp works is unverified.
  - Sources: [ggml-org GGUF](https://huggingface.co/ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF); [cicaba fixed GGUF](https://huggingface.co/cicaba/Qwen3-Reranker-0.6B-GGUF-llamacpp-fixed); [Voodisss GGUF](https://huggingface.co/Voodisss/Qwen3-Reranker-0.6B-GGUF-llama_cpp)

### Inferences
- The lowest-friction path on Windows with Python 3.14 is sentence-transformers ≥6.2 `CrossEncoder`, in fp16/bf16, with SDPA attention. Both Qwen3-Reranker-0.6B and bge-reranker-v2-m3 work this way with no remote code. Swapping the model ID in the existing CrossEncoder code path is then almost a drop-in change. The exception is the instruction prompt for Qwen.
- To run Qwen3-Reranker-4B within 6 GB, there are two options:
  - A GGUF build through llama.cpp's server. This adds an external binary and conversion-quality risk.
  - A 4-bit bitsandbytes load in transformers. Windows support for bitsandbytes and CUDA 13 wheels was not verified in this session.

### Gaps
- I did not confirm wheel availability for torch 2.14 with cu130 on Python 3.14 for the extra pieces: flash-attn, bitsandbytes, llama-cpp-python CUDA builds.
- I did not check for official ONNX exports of Qwen3-Reranker or bge-reranker-v2-m3.

## 6. Licenses (the project will be a public open-source repository)

### Takeaway
Qwen3-Reranker, bge-reranker-v2-m3, mxbai-rerank-v2 and gte-multilingual-reranker are Apache-2.0, which is safe. The jina v2, v3 and v3.5 rerankers are CC BY-NC 4.0, so they can be an optional, user-downloaded choice at most, never the default. The NVIDIA rerankers use OpenMDW-1.1, and the 1B adds Llama 3.2 Community License terms.

### Cited Findings
- **Apache-2.0:**
  - Qwen3-Reranker 0.6B/4B/8B — [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B); [recal.so](https://www.recal.so/blog/best-local-reranker-models-2026)
  - bge-reranker-v2-m3 — [bge card](https://huggingface.co/BAAI/bge-reranker-v2-m3)
  - mxbai-rerank v2 — [mxbai card](https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v2)
  - gte-multilingual-reranker — [gte card](https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base)
  - bge-reranker-v2-gemma, per recal.so — [recal.so](https://www.recal.so/blog/best-local-reranker-models-2026)
- **CC BY-NC 4.0:**
  - jina-reranker-v2-base-multilingual — [recal.so](https://www.recal.so/blog/best-local-reranker-models-2026)
  - jina-reranker-v3 — [jina v3](https://huggingface.co/jinaai/jina-reranker-v3)
  - jina-reranker-v3.5 — [jina v3.5](https://huggingface.co/jinaai/jina-reranker-v3.5)
- **NVIDIA:**
  - llama-nemotron-rerank-1b-v2: OpenMDW-1.1 plus the Llama 3.2 Community License, described as "ready for commercial use" — [card](https://huggingface.co/nvidia/llama-nemotron-rerank-1b-v2)
  - Nemotron-3.5-Rerank-8B: OpenMDW-1.1 — [card](https://huggingface.co/nvidia/Nemotron-3.5-Rerank-8B-BF16)
- **The current NLI model (cross-encoder/nli-deberta-v3-base):** its license was not checked in this session.

### Inferences
- The repository downloads weights at runtime and does not redistribute them. Even so, defaulting to a CC BY-NC model would pass a non-commercial restriction on to users. An Apache-2.0 model is the clean default.

### Gaps
- I did not read the full OpenMDW-1.1 text.
- I did not verify the bge-reranker-v2-gemma license directly on its card, where Gemma terms might apply.

## 7. Ranked recommendation for this hardware

### Takeaway
1. **Default: Qwen3-Reranker-0.6B.** Apache-2.0, about 1.2 GB in bf16, 32k context, works with sentence-transformers `CrossEncoder`, accepts English instructions, and is the strongest Apache model of its size on MMTEB-R and MLDR in Qwen's table.
2. **Fast or fallback baseline, and A/B partner: bge-reranker-v2-m3.** Apache-2.0, a classic encoder cross-encoder that is probably faster at 512 tokens. It was the best reranker on Russian RusBEIR and leads MIRACL in Jina's v3 table, but it falls below a strong embedder in Qwen's table.
3. **High-quality offline mode: Qwen3-Reranker-4B, quantized** (GGUF Q4/Q5 through llama.cpp, or 4-bit). It tops every table among Apache models but is estimated at 10–40 s per 100 chunks on this GPU.
4. **Alternatives:**
   - mxbai-rerank-large-v2 (Apache, about 1.5–2B, fits in bf16) has strong BEIR but mixed multilingual numbers.
   - llama-nemotron-rerank-1b-v2 is strong cross-lingually (MLQA) and in aimultiple's test, but supports Linux only, needs `trust_remote_code`, and adds Llama license terms.
   - jina-reranker-v3.5 has the best quality-to-size ratio in Jina's tables, but is CC BY-NC, so it should be an opt-in only.
5. **Not recommended:**
   - Nemotron-3.5-Rerank-8B and Qwen3-VL-Reranker: too large or multimodal, with no text benefit shown.
   - gte-multilingual-reranker-base and jina-v2: they underperform a strong embedder and jina-v2 is non-commercial.
   - Closed APIs: Cohere Rerank 5, Voyage rerank-3, Zerank.
   - Keeping nli-deberta-v3-base: it is the wrong model type.

### Cited Findings
- Supporting evidence is in sections 2–6: [Qwen card](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B); [jina v3.5 card](https://huggingface.co/jinaai/jina-reranker-v3.5); [RusBEIR](https://arxiv.org/pdf/2504.12879); [recal.so](https://www.recal.so/blog/best-local-reranker-models-2026)

### Inferences
- Whether a reranker helps at all depends on the first-stage embedder. If the project uses a strong multilingual embedder such as Qwen3-Embedding or bge-m3, verify that the reranker beats embedder-only ranking on a small labelled Russian-to-English set before enabling it by default.
- Suggested local check:
  - Use 30–50 queries and rerank the top-50 candidates.
  - Compare four configurations: embedder only, bge-v2-m3, Qwen3-0.6B, and Qwen3-4B quantized.
  - Record nDCG@10 or Hit@k, plus wall time on the RTX 3060.

### Gaps
- The ranking between options 1 and 2 cannot be settled from published data, because the benchmarks conflict and none of them is Russian-to-English. It needs a local measurement.
