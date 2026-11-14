# Multilingual text embedding models for a local RAG system (state as of November 2026)

Scope: models that could replace the current English-only concatenation of `BAAI/bge-large-en-v1.5` + `allenai/scibert_scivocab_uncased` (chosen spring 2025). Constraints: RTX 3060 Laptop 6 GB VRAM (Ampere, sm_86), 16 GB RAM, Windows 11 without WSL, Python 3.14.10, torch 2.14.1+cu130, one model loaded at a time, offline document batches plus one query at a time, mostly English scientific documents plus Russian/Slovak, Russian queries, cross-lingual retrieval required, public open-source repository.

Research date: 2026-11-14. No weights were downloaded and nothing was installed. Search budget was limited (about 18 tool calls), so several numbers come from vendor model cards or secondary coverage. Each finding says which. Policy check (AI_ORCHESTRATION.md, Subagent Duties): the task matches tier 3 (sources contradict, options must be compared). No tier-4 condition applies because the work is read-only research.

## Which models lead retrieval in late 2026, and when were they released?

### Takeaway
The 2026 open-weight leaders on MTEB Multilingual v2 are Microsoft harrier-oss-v1 (27B / 0.6B / 270M, about March–April 2026, MIT), Tencent KaLM-Embedding-Gemma3-12B, NVIDIA Nemotron-3-Embed (July 2026), jina-embeddings-v5-text (Feb 2026, non-commercial license) and IBM Granite Embedding Multilingual R2 (May 2026, Apache 2.0). Qwen3-Embedding (June 2025) is still the most-cited open baseline. For a 6 GB GPU the relevant tier is the sub-1.2B models: harrier-oss-v1-0.6b, Qwen3-Embedding-0.6B, Nemotron-3-Embed-1B, jina-v5-text-small/nano, granite-311m-r2, EmbeddingGemma (1 and 2) and BGE-M3.

### Cited Findings
- **harrier-oss-v1 (Microsoft):** three sizes. 270M has 640 dims and MTEB v2 66.5. 0.6B has 1,024 dims and MTEB v2 69.0. 27B has 5,376 dims and MTEB v2 74.3. All have 32,768-token context and MIT license. They are decoder-only with last-token pooling, the HF tag is `gemma3_text`, and the 270m/0.6b variants are distilled from larger models. — [HF model card harrier-oss-v1-270m](https://huggingface.co/microsoft/harrier-oss-v1-270m)
- Harrier release date: secondary coverage puts it at March 30, 2026 to early April 2026. Japanese press is dated April 9, 2026. The 27B model was reported #1 on Multilingual MTEB v2 (131 tasks) at release, ahead of Gemini Embedding 2. Language count conflicts: >100 per the announcement, 94 per the HF pages. — [Neowin](https://www.neowin.net/news/microsofts-new-harrier-models-top-benchmarks-outperforming-googles-gemini-embedding-2/); [Forest Watch (JP)](https://forest.watch.impress.co.jp/docs/news/2100348.html); [Microsoft Foundry Labs](https://labs.ai.azure.com/projects/harrier-oss-v1/); [MS Tech Community, April 2026](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/whats-new-in-foundry-labs---april-2026/4509714)
- An October 2026 guide reports harrier-oss-v1-27b leading MTEB Multilingual v2 with 74.27. A July 2026 source said KaLM-Embedding-Gemma3-12B (Tencent) was #1 at 72.32. Both are aggregator snapshots and were not verified against the live leaderboard. — [search summary of Medium / morphllm / premai guides](https://deepakjais.medium.com/which-embedding-model-should-you-use-a-scenario-based-guide-f3493869f305)
- **Qwen3-Embedding (Alibaba):** arXiv v3 dated 11 Jun 2025 (older information). Sizes 0.6B/4B/8B, 32K context, MRL (custom output dims), Apache 2.0. On the MTEB Multilingual mean (task), 0.6B scores 64.33, 4B 69.45 and 8B 70.58. The leaderboard snapshot for compared models is June 4, 2025. — [Qwen3 Embedding paper](https://arxiv.org/html/2506.05176v3)
- **NVIDIA Nemotron-3-Embed-1B:** released July 16, 2026. 1.14B params, pruned from Ministral-3-3B-Instruct and distilled from an 8B embedding teacher. 2048 dims, which can be sliced to 1024/512 (re-normalize after slicing), 32,768 context, license OpenMDW-1.1 ("ready for commercial use"). Russian is in its 34-language list; Slovak is not. — [NVIDIA build model card](https://build.nvidia.com/nvidia/nemotron-3-embed-1b.md)
- A multimodal successor, Nemotron-3.5-Embed-1B (October 2026), shares the text embedding space with Nemotron-3-Embed-1B. An 8B Nemotron-3-Embed also exists per one aggregator. — [NVIDIA build 3.5 card](https://build.nvidia.com/nvidia/nemotron-3_5-embed-1b/modelcard); [search summary incl. bentoml/openrouter guides](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models)
- **jina-embeddings-v5-text (Jina AI / Elastic):** announced Feb 19, 2026. *small* has 677M params, base Qwen3-0.6B-Base, 32K context, 1024 dims, Matryoshka 32–1024. *nano* has 239M params, base EuroBERT-210m, 8K context, 768 dims. Four LoRA task adapters. License table shows CC BY-NC 4.0. — [Jina AI announcement](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings); [arXiv 2602.15547](https://arxiv.org/html/2602.15547v1); [Elastic press release](https://ir.elastic.co/news/news-details/2026/Elastic-Introduces-Best-in-Class-Embedding-Models-for-High-Performance-Semantic-Search/default.aspx)
- Parameter counts for jina v5 conflict: the arXiv Table 1 gives 596M/212M (base models), while the announcements give 677M/239M (full models). — [arXiv 2602.15547](https://arxiv.org/html/2602.15547v1); [Jina](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings)
- **IBM granite-embedding-multilingual-r2:** blog post published May 14, 2026. Sizes 311M (768 dims, Matryoshka 512/384/256/128) and 97M (384 dims, no MRL). 32,768 context, Apache 2.0. Technical report is arXiv 2605.13521. — [HF blog, IBM Granite](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)
- **EmbeddingGemma 2 (Google):** released Oct 6, 2026, on the Gemma 4 architecture. 740M params total, with a 270M text-only configuration plus optional vision (170M) and audio (300M) encoders. 8K context, 768 dims with MRL to 512/256/128, Apache 2.0. Google claims multilingual text quality equal to EmbeddingGemma 1 but gives no MMTEB number in the post. — [Google blog](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/)
- **Older models still in comparisons:** BGE-M3 (2024, 568M, 8K context, 1024 dims, MIT, dense + sparse + multi-vector). — [premai 2026 guide](https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/); [M3-Embedding paper (Feb 2024)](https://arxiv.org/pdf/2402.03216)
- jina-embeddings-v3 (570M, 8K, CC-BY-NC-4.0, older) and NV-Embed-v2 (7.85B, CC-BY-NC-4.0, older). — [premai 2026 guide](https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/)
- A July 2026 arXiv paper, "DenseOn with the LateOn", introduces fully open dense and late-interaction models for multilingual, long-context and code search. It was not examined in detail. — [arXiv 2607.27178](https://arxiv.org/pdf/2607.27178)

### Inferences
- Harrier, Nemotron-3, jina-v5, granite-r2 and EmbeddingGemma-2 are all 2026 releases newer than the spring-2025 setup. Several of them claim to beat Qwen3-Embedding-0.6B at the same or smaller size.
- 27B, 12B and 8B models are out of practical reach on 6 GB VRAM, except heavily quantized 8B (see the practical-properties section).

### Gaps
- No direct read of the live MTEB leaderboard (HF Space) for November 2026, so current exact ranks are unverified.
- The KaLM-Embedding-Gemma3-12B release date and license were not verified.
- No primary source was found for Voyage, Cohere, Nomic or Snowflake open releases in 2026. Snowflake arctic-embed-m-v2.0 appears only as a baseline in IBM's table.
- DenseOn/LateOn scores and license were not checked.

## Retrieval scores: MMTEB multilingual, cross-lingual (RU query to EN docs), Russian benchmarks, scientific domain; contamination

### Takeaway
On MTEB Multilingual retrieval, small 2026 models (harrier-270m 66.4, granite-311m-r2 65.2) already match or exceed Qwen3-Embedding-0.6B (64.64). Nemotron-3-Embed-1B claims 71.05 on MMTEB Retrieval, and Qwen3-Embedding-8B scores 70.88. These numbers come from different papers and leaderboard dates, so they are only roughly comparable. No source gives Russian-to-English cross-lingual numbers for the 2026 models, and none gives ruMTEB scores for Qwen3/Harrier/Nemotron. The latest Russian-specific data covers BGE-M3 and mE5 (2024). Scientific retrieval (SciFact/SCIDOCS) per model was not found in 2026 sources.

### Cited Findings
- **MMTEB retrieval (Qwen3 paper, June 2025 snapshot, older):**

  | Model | Retrieval |
  |---|---|
  | Qwen3-0.6B | 64.64 |
  | Qwen3-4B | 69.60 |
  | Qwen3-8B | 70.88 |
  | Gemini Embedding | 67.71 |
  | gte-Qwen2-1.5B | 60.78 |
  | GritLM-7B | 58.31 |
  | mE5-large-instruct | 57.12 |
  | NV-Embed-v2 | 56.72 |
  | BGE-M3 | 54.60 |

  MTEB English v2 retrieval: Qwen3-0.6B 61.83, 4B 68.46, 8B 69.44, mE5-large-instruct 53.47. — [Qwen3 Embedding paper](https://arxiv.org/html/2506.05176v3)
- **MTEB Multilingual Retrieval, 18 tasks (IBM, May 2026):**

  | Model | Retrieval |
  |---|---|
  | harrier-oss-v1-270m | 66.4 |
  | granite-311m-r2 | 65.2 |
  | jina-v5-text-nano | 63.3 |
  | embeddinggemma-300m | 62.5 |
  | granite-97m-r2 | 60.3 |
  | gte-multilingual-base | 57.2 |
  | arctic-embed-m-v2.0 | 54.8 |
  | multilingual-e5-large | 53.7 |
  | text-embedding-3-small | 50.7 |

  Other granite-311m-r2 scores: LongEmbed 71.7, English retrieval (10 tasks) 52.6. — [IBM Granite R2 blog](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)
- **Nemotron-3-Embed-1B, NDCG@10 at seq len 4096 (vendor):** MMTEB Retrieval 71.05, RTEB(16) 72.38. The previous llama-nemotron-embed-1b-v2 scored 59.58 and 60.47. The NVFP4 quantized variant scores 70.59 MMTEB-R. — [NVIDIA model card](https://build.nvidia.com/nvidia/nemotron-3-embed-1b.md)
- **jina-v5-text MMTEB (131 tasks):** small 67.0 and nano 65.5, against Qwen3-0.6B (with instructions) at 64.3. MTEB English: small 71.7, nano 71.0. The five-benchmark retrieval average (MTEB-ML, MTEB-EN, RTEB, BEIR, LongEmbed) is 63.28 for small and 63.62 for jina-v4 (3.8B). Small ranked #8 on MTEB Multilingual v2 on Feb 21, 2026. — [Jina AI](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings)
- **Harrier MTEB Multilingual v2 means:** 66.5 (270m), 69.0 (0.6b), 74.3 (27b). The model card shows no retrieval subscore. — [HF harrier-oss-v1-270m](https://huggingface.co/microsoft/harrier-oss-v1-270m)
- **Cross-lingual:** granite-311m-r2 scores Belebele 66.5 and MLQA 67.1 (multilingual cross-lingual QA retrieval), against R1-278m at 62.2 and 63.0. The source gives no per-pair RU to EN breakdown. — [IBM Granite R2 blog](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)
- **ruMTEB (2024 paper, older):** retrieval BGE-M3 74.8 and mE5-large 74.0. Reranking 69.7 and 69.6. Overall averages 60.8 and 60.4. The paper notes a clear gap between instruct and non-instruct models. — [ruMTEB paper, arXiv 2408.12503](https://arxiv.org/html/2408.12503v1)
- GigaEmbeddings (ai-sage, Giga-Embeddings-instruct) claimed state-of-the-art ruMTEB 69.1 as of December 2024. Its table could not be extracted, and its model license was not checked. — [GigaEmbeddings, arXiv 2510.22369](https://arxiv.org/pdf/2510.22369)
- RusBEIR (Nov 2025) found that mE5-large and BGE-M3 beat BM25 on Russian full-document retrieval. — [RusBEIR, arXiv 2511.05079](https://arxiv.org/pdf/2511.05079)
- **Scientific domain:** a 2026 hybrid-retrieval study reports dense SciBERT at about 0.320 NDCG@10 on SciFact, below SPECTER and SciNCL. The best SciDocs NDCG@10 in that study is 0.178 (SciNCL). — [Applied Sciences 2026, doi 10.3390/app16104813](https://doi.org/10.3390/app16104813)
- **Contamination:** the Qwen3 paper does not discuss decontamination. MLDR and CodeSearchNet appear both in its SFT data and in its evaluation sets, and the 150M synthetic pairs come from the Qwen3 pretraining corpus with no stated overlap check. — [Qwen3 Embedding paper](https://arxiv.org/html/2506.05176v3)
- Harrier 270m/0.6b, Nemotron-3-1B and jina-v5 are distilled from larger embedding teachers. — [Harrier card](https://huggingface.co/microsoft/harrier-oss-v1-270m); [NVIDIA card](https://build.nvidia.com/nvidia/nemotron-3-embed-1b.md); [Jina](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings)
- Aggregators mix MMTEB, MTEB Multilingual and v2 scores, so their numbers are not directly comparable. — [search summary, premai/morphllm guides](https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/)

### Inferences
- MTEB-style public benchmarks are training targets for every vendor. Distilled small models (Harrier, Nemotron, jina-v5) inherit their teachers' benchmark-tuned behaviour. A 0.6B model at 69.0 MTEB-ML v2 is plausible but should be checked on the project's own RU-query / EN-doc set.
- Because no RU to EN cross-lingual or ruMTEB numbers exist for the 2026 models, a small in-house evaluation (for example 50–200 Russian questions over the English/scientific corpus, Recall@k and nDCG@10) is the only reliable way to choose among the top 3–4 candidates.
- SciBERT's roughly 0.32 SciFact NDCG@10 is far below what general modern embedders are typically reported to reach on BEIR SciFact (around 0.7). No 2026 source with that number was fetched, so treat the comparison as indicative only.

### Gaps
- No ruMTEB/encodechka scores were found for Qwen3-Embedding, Harrier, Nemotron-3, jina-v5, granite-r2 or EmbeddingGemma.
- No explicit RU-query to EN-document benchmark numbers were found (only aggregate Belebele/MLQA for Granite).
- Per-model SciFact/SCIDOCS numbers for the 2026 models were not retrieved. They exist inside MTEB(eng) results on the leaderboard but were not fetched.
- No Slovak-specific results were found.

## Practical properties on a 6 GB laptop GPU (params, VRAM, throughput, context, dims/MRL, prefixes, sparse/hybrid)

### Takeaway
Every sub-1.2B candidate fits in bf16 within 6 GB with room for batching. Qwen3-4B needs 8-bit or 4-bit quantization, and 8B fits only at about 4-bit with little headroom. Long context (32K) is offered by Harrier, Qwen3, Nemotron-3, jina-v5-small and granite-r2. EmbeddingGemma-2 offers 8K, and BGE-M3 and jina-v5-nano offer 8K. BGE-M3 is still the only mainstream candidate with built-in sparse and ColBERT outputs.

### Cited Findings

| Model | Params | Context | Dims / truncation | Query/doc prefixes | Source |
|---|---|---|---|---|---|
| harrier-oss-v1-0.6b | 0.6B | 32,768 | 1,024; MRL not mentioned | Query needs `Instruct: {task}\nQuery: {query}`; docs have no instruction. Omitting it degrades results. Preset prompts include `web_search_query` and `bitext_query`. | [HF card](https://huggingface.co/microsoft/harrier-oss-v1-270m) |
| harrier-oss-v1-270m | 270M | 32,768 | 640 | Same as 0.6b | [HF card](https://huggingface.co/microsoft/harrier-oss-v1-270m) |
| Qwen3-Embedding-0.6B / 4B / 8B | 0.6B / 4B / 8B | 32K | 1024 / 2560 / 4096; MRL | Query is `{Instruction} {Query}<\|endoftext\|>`; docs unchanged; EOS pooling | [paper](https://arxiv.org/html/2506.05176v3) |
| Nemotron-3-Embed-1B | 1.14B | 32,768 | 2048, sliceable to 1024/512 | Not documented | [NVIDIA card](https://build.nvidia.com/nvidia/nemotron-3-embed-1b.md) |
| jina-v5-text-small | 677M | 32K | 1024, MRL 32–1024 | `Query:` / `Document:`; retrieval LoRA selected via a per-task repo | [Jina](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings) |
| jina-v5-text-nano | 239M | 8K | 768, MRL 32–768 | Same as small | [Jina](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings) |
| granite-311m-multilingual-r2 | 311M | 32,768 | 768, MRL 512/384/256/128 | Not stated in blog | [IBM](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2) |
| EmbeddingGemma 2 | 270M text-only (740M full) | 8K | 768, MRL 512/256/128 | Not stated in blog | [Google](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/) |
| BGE-M3 | 568M | 8,192 | 1024 | None; dense + sparse + multi-vector | [premai](https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/); [M3 paper](https://arxiv.org/pdf/2402.03216) |

- Quantization: Nemotron-3-Embed-1B has an NVFP4 variant keeping about 99.5% of the RTEB score. NVFP4 is a Blackwell-oriented format, so it is likely not useful on Ampere (inference). — [NVIDIA card](https://build.nvidia.com/nvidia/nemotron-3-embed-1b.md)
- jina-v5 ships 14 GGUF quants (F16 to IQ1_S) plus MLX 4/8-bit. — [Jina](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings)
- The HF harrier page lists 22 quantized variants of unspecified format. — [HF card](https://huggingface.co/microsoft/harrier-oss-v1-270m)
- EmbeddingGemma 2 quantized needs about 191 MB of RAM text-only on a phone. — [Google](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/)
- Throughput: granite 311M encodes about 1,800 docs/s and 97M about 2,500 docs/s on an H100 with 512-token chunks. No laptop-GPU figures were found. — [IBM](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)
- Long-context quality: granite-311m-r2 scores LongEmbed 71.7. — [IBM](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)

### Inferences
- **bf16 weight memory, about 2 bytes per parameter (rule-of-thumb estimate, not measured):** harrier-0.6b / Qwen3-0.6B / jina-v5-small are about 1.2–1.4 GB. Nemotron-1B is about 2.3 GB. BGE-M3 is about 1.1 GB. granite-311m is about 0.6 GB. Qwen3-4B is about 8 GB, which does not fit in bf16. It needs Q8 (about 4.3 GB) or Q4 (about 2.5 GB) via GGUF or bitsandbytes. Qwen3-8B at Q4 is about 5 GB, which is tight. Activation memory grows with batch × sequence length, so 32K-token chunks need batch size 1 and SDPA/flash attention even for 0.6B models.
- On an RTX 3060 Laptop (roughly 1/10–1/15 of H100 bf16 throughput), 0.3–0.6B models at 512 tokens are expected to run on the order of 100–300 docs/s. This is an extrapolation, not a measurement. Single-query latency for a 0.6B model should be well under 100 ms.
- The instruction prefix is mandatory for Harrier and Qwen3 queries, and jina-v5 uses `Query:`/`Document:`. The pipeline must store the prefix config alongside the index.

### Gaps
- No measured throughput or VRAM numbers on a 6 GB Ampere laptop GPU for any candidate.
- Harrier MRL support and its native release date on HF were not confirmed in the model card.
- Prefix formats for granite-r2 and EmbeddingGemma-2 were not retrieved.
- Whether Nemotron-3-Embed-1B has an HF transformers/sentence-transformers path (the NVIDIA card lists only a Rust/NIM runtime on Linux). The [litert-community mirror](https://huggingface.co/litert-community/Nemotron-3-Embed-1B) suggests HF availability, but this was not verified.

## Compatibility: sentence-transformers/transformers on Python 3.14 + torch 2.14 + CUDA 13.0 on Windows; flash-attention; GGUF/ONNX

### Takeaway
sentence-transformers 6.2.0 (Oct 21, 2026) officially supports Python 3.14. The sub-1B candidates load with standard `SentenceTransformer(...)` and do not require flash-attention. GGUF exists for jina-v5 and EmbeddingGemma-2. Granite-r2 ships ONNX/OpenVINO. Nemotron-3's documented runtime is Linux/NIM only.

### Cited Findings
- sentence-transformers 6.2.0 added Python 3.14 and huggingface_hub 2.x support, with Requires-Python >=3.10. It was released Oct 21, 2026 per a PyPI mirror. — [newreleases.io 6.2.0](https://newreleases.io/project/pypi/sentence-transformers/release/6.2.0); [CERN PyPI mirror](https://simple-repository.app.cern.ch/project/sentence-transformers)
- Harrier loads via `SentenceTransformer("microsoft/harrier-oss-v1-270m", model_kwargs={"dtype": "auto"})` or `AutoModel`. The card states no flash-attention requirement and no minimum transformers version. — [HF card](https://huggingface.co/microsoft/harrier-oss-v1-270m)
- Granite R2 supports sentence-transformers (recommended path). Pre-converted ONNX and OpenVINO weights are shipped. GGUF is not shipped but can be converted with llama.cpp. Flash Attention 2 is supported but not required. — [IBM](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)
- jina-v5 has a sentence-transformers example with a per-task repo (for example `jina-embeddings-v5-text-small-retrieval`), `prompt_name="query"/"document"` and bf16. GGUF works via llama.cpp with `--pooling last`, plus vLLM and MLX. — [Jina](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings)
- EmbeddingGemma 2 is supported in transformers, sentence-transformers, llama.cpp (GGUF), Ollama, LM Studio, vLLM, SGLang, MLX and transformers.js. — [Google](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/)
- The Nemotron-3-Embed-1B card lists a Rust runtime engine, Linux as the preferred/supported OS, and Ampere among supported GPUs (A100/A10G). It does not specify transformers, flash-attention or sentence-transformers requirements. — [NVIDIA card](https://build.nvidia.com/nvidia/nemotron-3-embed-1b.md)

### Inferences
- On Windows, the flash-attn package has historically lacked official wheels. It is safer to rely on PyTorch's built-in SDPA (`attn_implementation="sdpa"`), which works on sm_86 and needs no extra install. None of the main candidates documents a hard flash-attn requirement.
- Decoder-based models (Harrier with a Gemma3 backbone, Qwen3, jina-v5-small with a Qwen3 backbone) need a transformers version that knows the architecture. Gemma3 and Qwen3 have been in transformers since 2025, so a 2026 transformers should work, but this is unverified for torch 2.14/cu130 on Windows.
- Nemotron-3-Embed-1B carries the highest compatibility risk on Windows.

### Gaps
- No direct confirmation that torch 2.14.1+cu130 Windows wheels work with transformers on Python 3.14 for these specific architectures.
- No check of `trust_remote_code` requirements for jina-v5, Nemotron or granite-r2.
- Harrier GGUF/ONNX formats are unknown.

## License (public open-source repository)

### Takeaway
MIT (Harrier, BGE-M3) and Apache 2.0 (Qwen3-Embedding, Granite R2, EmbeddingGemma 2) are unproblematic. Nemotron-3 uses NVIDIA's OpenMDW-1.1, stated as commercial-use-ready. jina-embeddings-v5-text (and v3) are CC BY-NC 4.0, so downstream users of the open-source repository could not use them commercially.

### Cited Findings
- Harrier: MIT. — [HF card](https://huggingface.co/microsoft/harrier-oss-v1-270m)
- Qwen3-Embedding: Apache 2.0. — [paper](https://arxiv.org/html/2506.05176v3)
- Granite R2: Apache 2.0. — [IBM](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)
- EmbeddingGemma 2: Apache 2.0. — [Google](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/)
- BGE-M3: MIT. — [premai](https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/)
- Nemotron-3-Embed-1B: OpenMDW-1.1, "ready for commercial use". Its base model Ministral-3-3B is Apache 2.0. — [NVIDIA card](https://build.nvidia.com/nvidia/nemotron-3-embed-1b.md)
- jina-v5-text: CC BY-NC 4.0, shown as a shared table cell. It is unclear whether this explicitly covers nano. — [Jina](https://jina.ai/news/jina-embeddings-v5-text-distilling-4b-quality-into-sub-1b-multilingual-embeddings)
- jina-v3 and NV-Embed-v2: CC-BY-NC-4.0. — [premai](https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/)

### Inferences
- The repository would not redistribute weights, only reference them. Even so, a default model under a non-commercial license limits downstream users, so jina-v5 should at most be an optional backend.
- The OpenMDW-1.1 text was not read, so redistribution and attribution terms should be checked before choosing Nemotron.

### Gaps
- Full OpenMDW-1.1 terms, the GigaEmbeddings license and the KaLM-Gemma3 license were not read. Gemma-derived models (Harrier's Gemma3 backbone) are MIT per Microsoft's card, but whether the Gemma terms propagate was not checked.

## Single strong multilingual model vs a general + domain (SciBERT-style) concatenation

### Takeaway
The available evidence favours a single modern multilingual retrieval-trained embedder. SciBERT is a masked LM, not a contrastively trained embedding model, and it scores low on scientific retrieval. Both current components are English-only, so the concatenation cannot do RU-to-EN cross-lingual retrieval at all. No 2025–2026 head-to-head of a "general + SciBERT concat" against a single modern model was found.

### Cited Findings
- Dense SciBERT scores about 0.320 NDCG@10 on SciFact, below the domain embedders SPECTER and SciNCL. — [Applied Sciences 2026](https://doi.org/10.3390/app16104813)
- General-purpose sentence encoders (MPNet, MiniLM) gave far better clustering than SciBERT in every scenario, and the paper concludes that specialized pretraining (SciBERT, SPECTER) does not guarantee better results than advanced general models. — [arXiv 2601.08841 (Jan 2026)](https://arxiv.org/html/2601.08841)
- SciBERT is not tuned for sentence/document embeddings, which likely explains why general embedders beat it. — [arXiv 2601.08841](https://arxiv.org/html/2601.08841); [arXiv 2510.06244, "Evaluating Embedding Frameworks for Scientific Domain"](https://arxiv.org/html/2510.06244)
- The ruMTEB authors observe a clear performance gap between instruct and non-instruct models. This supports instruction-tuned embedders such as Qwen3, Harrier and Nemotron over older non-instruct ones. — [ruMTEB paper](https://arxiv.org/html/2408.12503v1)

### Inferences
- The SciBERT component probably adds dimensionality and indexing cost with little retrieval gain. Replacing the pair with a single multilingual model removes the need to embed twice and tune concatenation weights.
- If domain signal is still wanted, a cheaper complement is hybrid retrieval: dense plus BM25 or a learned sparse model such as BGE-M3's sparse head. A multilingual reranker is another option. The 2026 hybrid scientific-retrieval study (app16104813) uses this pattern rather than embedding concatenation.

### Ranked recommendation for this hardware and these constraints (inference, based on the findings above)
1. **microsoft/harrier-oss-v1-0.6b**. MIT, 32K context, 1024 dims, MTEB-ML v2 69.0 (vendor), sentence-transformers path, about 1.2 GB bf16. Best quality-per-VRAM among permissively licensed models. Caveats: mandatory query instruction, no confirmed MRL, distillation and benchmark-fit risk, release about March–April 2026.
2. **Qwen/Qwen3-Embedding-0.6B**. Apache 2.0, 32K, MRL, MMTEB-R 64.64. The most battle-tested option (June 2025) with broad tooling and GGUF. It is the safe fallback. Qwen3-Embedding-4B in Q8/Q4 GGUF (MMTEB-R 69.60) is an option for the offline document pass if quality matters more than speed, with the same model at query time.
3. **ibm-granite/granite-embedding-311m-multilingual-r2**. Apache 2.0, 32K, MRL, MTEB-ML retrieval 65.2, LongEmbed 71.7, ONNX shipped. The fastest and smallest, with the best-documented cross-lingual numbers (Belebele/MLQA).
4. **NVIDIA Nemotron-3-Embed-1B**. Highest claimed MMTEB retrieval in the 1B class (71.05). Ranked lower here because of Windows/HF-runtime uncertainty and the less common OpenMDW license.
5. **BAAI/bge-m3**. Older (2024) and weaker on dense MMTEB retrieval (54.60), but the only candidate with native sparse and ColBERT outputs and good ruMTEB retrieval (74.8). Useful as a hybrid/lexical companion or baseline.
- **Not recommended as default:** jina-v5-text (CC BY-NC 4.0 despite strong scores); EmbeddingGemma 2 (no published MMTEB retrieval number yet; 8K context); 8B and larger models (VRAM).
- Choose among items 1–4 using a small in-house RU-query / EN-document evaluation, because public Russian and cross-lingual numbers are missing for all 2026 models.

### Gaps
- No direct 2025–2026 experiment comparing weighted general + SciBERT concatenation with a single multilingual embedder on SciFact/SCIDOCS or on cross-lingual data was found.
