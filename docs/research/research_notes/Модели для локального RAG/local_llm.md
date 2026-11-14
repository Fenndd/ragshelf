# Local LLMs for RAG answer generation on a 6 GB VRAM laptop GPU (RTX 3060 Laptop, 16 GB RAM, Windows 11), as of November 2026

Scope note: research only. Nothing was downloaded or installed. Research date: 2026-11-14. Many sources are SEO-style blogs, so primary sources (model cards, the Vectara leaderboard repository, the IBM blog, llama.cpp releases, Ollama docs) are given more weight, and conflicts are flagged where they appear. "Measured" means a number someone measured on real hardware. "Estimated" means a projection.

## 1. Which open-weight models are the strongest that fit 6 GB VRAM (fully or with offload into 16 GB RAM)? Release dates

### Takeaway
For 6 GB VRAM in late 2026, the strongest realistic candidates are **Qwen3.5-9B** (Alibaba, Feb/Mar 2026, Apache 2.0). It is borderline at 4-bit and needs IQ4_XS/Q4_K_S or offloading a few layers. Next come **Qwen3.5-4B** (same family, fits fully with room for a long context) and **Gemma 4 E4B** (Google, Apr 2026, Apache 2.0). **Granite 4.1 8B/3B** (IBM, Apr 29 2026) is a RAG-oriented alternative, but its supported-language list has no Russian. MoE models with about 3B active parameters (Qwen3.6-35B-A3B, Gemma 4 26B-A4B) are too large for 6 GB VRAM plus 16 GB RAM at Q4. No small dense Qwen3.6, 3.7 or 3.8 model was found.

### Cited Findings
**Qwen family (2026)**
- Qwen3.5 small dense models (0.8B, 2B, 4B, 9B) were released on March 2, 2026, with Instruct and Base variants, under Apache 2.0 — [Gigazine](https://gigazine.net/gsc_news/en/20260303-qwen-3-5-small); [Artificial Analysis, Mar 5 2026](https://artificialanalysis.ai/articles/qwen3-5-small-models). The HF model card citation says "February 2026" — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B). (Minor date conflict: the paper is dated Feb and the small models came out about Mar 2.)
- Qwen3.5-9B architecture: hybrid Gated DeltaNet (linear attention) plus Gated Attention, laid out as 8 × (3 DeltaNet + 1 full attention) = 32 layers. It has a vision encoder, a native context of 262,144 tokens (about 1M with YaRN), Apache-2.0, and claims 201 languages and dialects. Thinking is ON by default — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B).
- Qwen3.5-9B benchmarks from the model card: MMLU-Pro 82.5, GPQA Diamond 81.7, IFEval 91.5, IFBench 64.5, MMMLU 81.2, MMLU-ProX 76.3, WMT24++ 72.6, AA-LCR 63.0, LongBench v2 55.2 — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B).
- Artificial Analysis Intelligence Index (reasoning mode): Qwen3.5-4B = 27, Qwen3.5-9B = 32, Qwen3 4B 2507 = 18. Memory at 4-bit: 9B ≈ 6 GB, 4B ≈ 3 GB — [Artificial Analysis](https://artificialanalysis.ai/articles/qwen3-5-small-models). The non-reasoning 9B scores 27.3, per another site quoting AA — [localllm.in](https://localllm.in/blog/best-local-llms-8gb-vram-2025).
- Qwen3.6 open weights are Qwen3.6-35B-A3B (MoE, about 3B active, Apr 2026, Apache 2.0) and Qwen3.6-27B dense (Apr 22 2026). No Qwen3.6 4B or 9B was found — [Wikipedia: Qwen](https://en.wikipedia.org/wiki/Qwen); [cntechpost, Apr 17 2026](https://cntechpost.com/2026/04/17/alibaba-open-sources-qwen3-6-35b-a3b-rival-larger-ai-models-coding/); [NYU Shanghai RITS](https://rits.shanghai.nyu.edu/ai/qwen3-6-27b-a-dense-27b-model-that-beats-a-397b-moe-on-coding).
- Qwen3.8 (Aug 2026) open models are 27B dense (Apache 2.0, Aug 14 2026), Qwen3.8-Flash-Next 125B MoE (Qwen Community 1.0 license) and a 2.4T-A95B model. Wikipedia lists no small dense Qwen3.8 — [Wikipedia: Qwen](https://en.wikipedia.org/wiki/Qwen).

**Gemma 4**
- Gemma 4 launched with E2B, E4B, 26B A4B (MoE) and 31B dense, under Apache 2.0 (earlier Gemma versions used a custom license). The release date is Apr 2, 2026 per [9to5Google](https://9to5google.com/2026/04/02/google-gemma-4/) and [The Register](https://www.theregister.com/2026/04/02/googles_gemma_4_open_weights/). Other sources give Mar 31, 2026 ([Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/06/google-gemma-4-12b/)) or "Mar 2026" ([computingforgeeks](https://computingforgeeks.com/open-source-llm-comparison/)), so the date is a minor conflict.
- Gemma 4 E4B has 4.5B effective and 8B total parameters including Per-Layer Embeddings, with 128K context. E2B has 2.3B effective and 5.1B total. 26B A4B has 3.8B active and 25.2B total, with 256K context. Hybrid sliding-window (512 tokens on E4B) plus global attention. Pre-trained on 140+ languages, with out-of-the-box support for 35+. Thinking is enabled via `<|think|>` / `enable_thinking=True` — [HF gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it).
- Gemma 4 instruction-tuned scores (model card): MMLU-Pro E2B 60.0 / E4B 69.4 / 26B-A4B 82.6 / 31B 85.2. MMMLU 67.4 / 76.6 / 86.3 / 88.4. MRCR v2 8-needle 128k 19.1 / 25.4 / 44.1 / 66.4 — [HF gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it). One blog's E4B MMLU-Pro of 78.1% contradicts the card's 69.4% — [codersera](https://codersera.com/blog/gemma-4-vs-qwen-3-5-comparison-2026/).
- Gemma 4 12B ("Unified", dense, 11.95B params, 48 layers, 1,024-token sliding window, 256K context) was released Jun 3, 2026 — [Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/06/google-gemma-4-12b/); [HF google/gemma-4-12B](https://huggingface.co/google/gemma-4-12B).

**IBM Granite (RAG-oriented)**
- Granite 4.1 (3B, 8B, 30B) was released Apr 29, 2026. All are dense GQA transformers (not hybrid Mamba), under Apache 2.0, with context up to 512K for 8B/30B. Languages: EN, DE, ES, FR, JA, PT, AR, **CS**, IT, KO, NL, ZH. **Russian and Slovak are not listed** — [HF blog: Granite 4.1](https://huggingface.co/blog/ibm-granite/granite-4-1).
- Granite Switch 4.1 8B/30B was reported released Oct 14, 2026. Granite Guardian 4.1 8B checks RAG groundedness — [Unite.ai](https://www.unite.ai/?p=486771); [IBM Granite Guardian docs](https://www.ibm.com/fr-fr/granite/docs/models/guardian).

**Other 2026 small or small-active releases**
- From Oct 2026: LFM2.5-24B-A2B (Liquid AI, Oct 13, LFM Open License 1.0 with a revenue cap), Mellum2.1 Thinking (JetBrains, Oct 8, 12B/2.5B-active MoE, aimed at coding, Apache 2.0) and MiniCPM-V 4.7 35B-A3B (OpenBMB, Apache 2.0) — [computingforgeeks (updated Oct 24 2026)](https://computingforgeeks.com/open-source-llm-comparison/); [edenai](https://www.edenai.co/post/best-open-weight-llms). These are secondary sources and were not verified on model cards.
- Older models that are still relevant: Phi-4-mini 3.8B (Jan 2025, MIT), Qwen3 8B (Apr 2025, Apache 2.0) and gpt-oss-20b (Aug 2025, 21B/3.6B MoE, Apache 2.0) — [computingforgeeks](https://computingforgeeks.com/open-source-llm-comparison/). The comparison table lists no small Llama or Ministral rows for 2026 — [computingforgeeks](https://computingforgeeks.com/open-source-llm-comparison/).
- Mistral Ministral 3 3B/8B ("2512" = Dec 2025) appear on the Vectara leaderboard — [Vectara](https://github.com/vectara/hallucination-leaderboard).

**MoE with offload (Qwen3.6-35B-A3B)**
- A GitHub PR profile for a "6 GB RTX 3060" uses Unsloth UD-Q2_K_XL (12.3 GB) with 88% of the model on the CPU and gets about 4–5 tok/s, dropping to about 3 tok/s at 262K context with a q8_0 cache. The PR also mentions a T600, so the hardware is unclear — [GitHub PR #251](https://github.com/G3A/workshop-desarrollo-sw-guiado-por-ia/pull/251).
- On a 12 GB RTX 3060, Q4_K_M reaches about 26 tok/s, and `--n-cpu-moe` matters more than `-ngl` — [castlen3 guide](https://github.com/castlen3/rtx3060-qwen3.6-35b-guide). One calculator puts Q4_K_M weights at about 22 GB — [modelfit.io](https://modelfit.io/can-i-run/qwen3.6-35b-a3b-q4-on-rtx-3060/).

### Inferences
- With 6 GB VRAM plus about 14 GB usable RAM (about 20 GB in total, minus the OS and the Python process), a Q4 35B-A3B MoE (about 22 GB) does not fit. Only Q2/Q3 fits, with a quality loss and about 4–5 tok/s. Gemma 4 26B-A4B at Q4 (about 15–16 GB) would leave almost no RAM free. Neither is a practical choice for this laptop.
- Qwen3.5-9B is the strongest model in the "fits" class: its Intelligence Index (32) is well above Qwen3 4B (18) and older 8B models. Granite 4.1 lacks Russian, which counts against it for Russian answers.

### Gaps
- No exact Hugging Face publication date was confirmed for each Qwen3.5 small checkpoint. The Gemma 4 date conflict (Mar 31 vs Apr 2) was not resolved.
- No 2026 small Llama or SmolLM release was found. Search gave no evidence of a GLM small dense model in 2026, though GLM-4.6V-Flash and GLM-4.7-flash exist (see sections 2 and 4).
- Granite 4.1 8B instruct benchmark numbers beyond RULER were not collected.

## 2. RAG-specific quality: faithfulness, citations, refusal when the context lacks the answer, long context (8k–32k)

### Takeaway
No single 2026 benchmark covers all of the candidates. The Vectara hallucination leaderboard (updated Oct 22 2026) shows small dense models from the Qwen3, Gemma 3 and Granite 4 generations at about 4–6% hallucination on grounded summarization. In the same table, Qwen3.5-35B-A3B scores worse (10.5%) and Phi-4-mini and Ministral 3 score much worse (about 22–24%). Qwen3.5-4B and Qwen3.5-9B were not found on the leaderboard. For long context, Qwen3.5-9B publishes AA-LCR 63.0 and LongBench v2 55.2, and Granite 4.1 publishes RULER 83.6 at 32K for the 8B base model. Citation and refusal behavior must be enforced through the prompt and checked in the project's own evals.

### Cited Findings
- Vectara HHEM leaderboard (grounded summarization; last updated Oct 22, 2026). Each row gives hallucination rate / answer rate: Phi-4 (14B) 3.7% / 80.7%. Gemma-3-12B 4.4% / 97.4%. **Qwen3-8B 4.8% / 99.9%**. Mistral-small-2501 5.1%. Granite-4.0-h-small 5.2% / 100%. Gemma-4-26B-A4B 5.2% / 99.8%. **Qwen3-4B 5.7% / 99.9%**. Gemma-3-4B 6.4% / **67.3%**. Ministral-3b-2410 7.3%. Ministral-8b-2410 7.4%. GLM-4.7-flash 9.3%. **Qwen3.5-35B-A3B 10.5%**. Granite-3.3-8B 10.6%. Ministral-3-8b-2512 21.7%. Phi-4-mini 23.5%. Ministral-3-3b-2512 24.2%. The best overall is finix_s1_32b at 1.8% — [Vectara hallucination leaderboard](https://github.com/vectara/hallucination-leaderboard).
- FaithEval (Salesforce, ICLR 2025) has 4.9K problems across unanswerable, inconsistent and counterfactual contexts. Its main finding is that strong results on general benchmarks do not carry over to faithfulness with noisy contexts — [FaithEval arXiv 2410.03727](https://arxiv.org/html/2410.03727). A third-party leaderboard lists Qwen3-8B on FaithEval at 55.5 F1 / 23.8 EM with full context, rising to 74.9 F1 with the ProbeRAG method. The setup differs from the original paper — [SOTA2](https://www.sota2.com/research/sota/faithfulness-evaluation-on-faitheval). No FaithEval numbers were found for Qwen3.5, Gemma 4 or Granite 4.x.
- AA-Omniscience, which measures closed-book knowledge and hallucination, not RAG: Qwen3.5-4B has an 80% hallucination rate and Qwen3.5-9B 82%. This is closed-book behavior, so the small models rarely abstain when they lack knowledge — [Artificial Analysis](https://artificialanalysis.ai/articles/qwen3-5-small-models).
- Long context: Qwen3.5-9B AA-LCR 63.0 and LongBench v2 55.2 — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B). Gemma 4 MRCR v2 8-needle at 128k: E4B 25.4%, 26B-A4B 44.1% — [HF gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it). Granite 4.1 RULER (base) for 3B/8B/30B: 75.0/83.6/85.2 at 32K and 58.0/73.0/76.7 at 128K — [HF blog Granite 4.1](https://huggingface.co/blog/ibm-granite/granite-4-1).
- Granite 4.1 SFT data curation flagged responses not grounded in the retrieved context as hallucinations. No built-in citation feature for 4.1 is described. A citation adapter existed for Granite 3.2 — [HF blog Granite 4.1](https://huggingface.co/blog/ibm-granite/granite-4-1); [arXiv 2504.11704](https://arxiv.org/pdf/2504.11704v1).
- Qwen3.5-9B instruction following: IFEval 91.5 and IFBench 64.5 — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B). These are relevant to following "cite [n]" and "say you don't know" instructions.

### Inferences
- Within the Vectara table, the Qwen family gives a high answer rate (99.9%) with low hallucination at 4B–8B. That suggests Qwen3.5-4B/9B probably behave similarly, but this is not measured. Gemma 3 4B's 67% answer rate suggests the Gemma small models refuse or deflect more often. That can help "refuse when the context lacks the answer" but can hurt coverage.
- Phi-4-mini and Ministral 3 (2512) score poorly on grounded summarization (about 22–24%), so they should be ranked low for RAG.
- At 8–32K tokens of retrieved text, every candidate is far inside its native window. Hybrid or linear-attention designs (Qwen3.5, Gemma 4 sliding window) keep the KV cache small (section 4).

### Gaps
- No faithfulness, citation or refusal benchmark (FaithEval, RAGTruth, ContextualBench, CRAG) was found for Qwen3.5-4B/9B, Gemma 4 E4B/12B or Granite 4.1. The project should run its own small eval with answerable and unanswerable questions over its own corpus.
- No RULER numbers were found for Qwen3.5 small or Gemma 4 small models.

## 3. Quality in Russian (and Slovak) when writing answers from English sources; MERA

### Takeaway
No MERA scores for Qwen3.5 small, Gemma 4 or Granite 4.1 could be retrieved, because the leaderboard renders client-side. The only multilingual signals are vendor numbers. Qwen3.5-9B scores MMMLU 81.2 and WMT24++ 72.6 and claims 201 languages. Gemma 4 E4B scores MMMLU 76.6 and claims 140+ pre-training languages. Granite 4.1 lists Czech but **not Russian or Slovak**. Qwen3.5-9B is the safest pick on published multilingual numbers. A one-off anecdote favors Gemma 3 4B's Russian, so Gemma 4 E4B is worth an A/B test.

### Cited Findings
- MERA added a Text 2.0 leaderboard (Sep 1, 2026; 12 new private tests in Human-Centric, Culture-Specific, Agentic and Reasoning categories) and a MERA Reason leaderboard (Jul 24, 2026) — [MERA site](https://mera.a-ai.ru/en). The leaderboard page rendered no rows when fetched — [MERA leaderboard](https://mera.a-ai.ru/en/text/leaderboard).
- Qwen3.5-9B multilingual scores: MMMLU 81.2, MMLU-ProX 76.3, INCLUDE 75.6, WMT24++ 72.6, and 201 languages claimed. Russian and Slovak are not named individually — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B).
- Gemma 4 MMMLU: E2B 67.4, E4B 76.6, 26B-A4B 86.3, 31B 88.4. Pre-trained on 140+ languages, with 35+ supported out of the box — [HF gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it).
- Granite 4.1 languages exclude Russian and Slovak and include Czech — [HF blog Granite 4.1](https://huggingface.co/blog/ibm-granite/granite-4-1).
- An anecdotal CPU-only test called Gemma3:4b the clear winner for Russian and Qwen3.5:9b slow but stronger for complex reasoning. This is a single-machine anecdote — [DEV Community](https://dev.to/nigismo/running-llms-on-a-cpu-only-server-my-benchmark-of-gemma-qwen-spark-and-minicpm-3hig).
- POLLUX (a Russian generative evaluation, 2025) covers Gemma 3 but not the 2026 small models — [arXiv 2505.24616](https://arxiv.org/pdf/2505.24616).

### Inferences
- Small models in the 4B class tend to lose fluency and grammatical accuracy (case agreement) in Russian more than 9B models do. This is a common pattern, not measured here, so Qwen3.5-9B is preferred over the 4B models for Russian answers.
- Granite 4.1 should not be the main generator for Russian answers. It could still serve for English-only answers or as a checker.
- Slovak has no evidence from any source. Expect weaker quality than Russian for all small models.

### Gaps
- MERA numbers for any candidate: the leaderboard needs JavaScript, and its CSV/JSON export was not tried.
- No Slovak-specific benchmark was found for any candidate.
- No measurement was found of cross-lingual RAG (English chunks, Russian answer) faithfulness.

## 4. Quantization, VRAM, KV-cache memory (8k/16k/32k) and realistic tokens/s on an RTX 3060 Laptop 6 GB

### Takeaway
Qwen3.5's hybrid design keeps the KV cache tiny: measured at **128/256/512/1,024 MiB at 4K/8K/16K/32K** for the 9B with an FP16 cache. That is about 32 KiB per token, versus about 2,000 MiB at 32K for Gemma 3 12B and 2,560 MiB for Phi-4. The binding constraint is therefore the weights. Qwen3.5-9B Q4_K_M needed about 6.1 GB of physical VRAM at 4K on an 8 GB card, so on a 6 GB laptop it needs IQ4_XS (5.5 GB) or Q3_K_M, or a few layers on the CPU. Qwen3.5-4B Q4_K_M (about 2.7 GB) fits fully with 32K context. No measured numbers exist for an RTX 3060 *Laptop* 6 GB specifically.

### Cited Findings
- Measured on an RTX 3070 8 GB (desktop, 385.7 GB/s) with llama.cpp, Q4_K_M, `--flash-attn on`, `--fit on`. Qwen3.5-9B weights on GPU: 5,061 MiB. KV cache: 128 / 256 / 512 / 1,024 MiB at 4K / 8K / 16K / 32K. Physical VRAM: 6,117 / 6,245 / 6,493 / 7,013 MiB. Decode: 57.9 / 57.7 / 56.6 / 54.9 tok/s. Prefill: 1,932 tok/s at 4K. KV cache at 32K for comparison: Gemma 3 12B 2,000 MiB, Phi-4 14B 2,560 MiB, GLM-4.6V-Flash 1,152 MiB. Article updated Apr 1, 2026 — [localllm.in](https://localllm.in/blog/best-local-llms-8gb-vram-2025).
- The same source, on a Tesla T4 16 GB with Ollama: Qwen3.5-9B text-only Q4_K_M runs at about 750 tok/s prefill and 25–28 tok/s decode. The multimodal tag adds about 1.38 GB of VRAM for the vision encoder — [localllm.in](https://localllm.in/blog/best-local-llms-8gb-vram-2025).
- Qwen3.5-9B GGUF sizes (bartowski, llama.cpp b9222, includes MTP layers usable with `--spec-type draft-mtp` from b9180): Q3_K_M 5.18 GB, IQ4_XS 5.50 GB, Q4_K_S 5.86 GB, Q4_K_M 6.17 GB, Q5_K_M 7.11 GB, Q6_K 7.96 GB, Q8_0 9.80 GB — [bartowski GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF). Conflicting size for Q4_K_M: 5.68 GB — [runaihome](https://runaihome.com/blog/best-local-llm-6gb-vram-2026/). A likely cause is a different converter or the presence of MTP or vision tensors, but this is not verified.
- Qwen3.5-4B Q4_K_M is 2.74 GB, "16K+ comfortable" on 6 GB — [runaihome, Aug 13 2026](https://runaihome.com/blog/best-local-llm-6gb-vram-2026/). A 3.3 GB figure is also cited — [promptquorum](https://www.promptquorum.com/prompt-bites/best-local-llm-6gb-vram).
- Gemma 4 E4B decode speeds: 24.39 tok/s measured on an RTX 3050 Laptop and about 21 tok/s on an RTX 4060. About 5 GB of VRAM for the QAT build — [runaihome](https://runaihome.com/blog/best-local-llm-6gb-vram-2026/).
- Llama 3.2 3B Q4_K_M runs at 50.4 tok/s on an RTX 2060 6 GB. 7–8B models with spill-over to RAM run at 7–9 tok/s on an RTX 2060 — [runaihome](https://runaihome.com/blog/best-local-llm-6gb-vram-2026/).
- Qwen's claim of "near-lossless" accuracy with 4-bit weights and a 4-bit KV cache is quoted but not tested by the article — [localllm.in](https://localllm.in/blog/best-local-llms-8gb-vram-2025).

### Inferences
- An RTX 3060 Laptop GPU has 6 GB on a 192-bit bus. Memory bandwidth is roughly 336 GB/s depending on the OEM TGP and clocks; this is a hardware spec not verified in this session. Windows and the display take a few hundred MB unless the iGPU drives the display. That leaves an estimated **5.3–5.7 GB usable**.
- Plan for Qwen3.5-9B: IQ4_XS (5.5 GB) or Q4_K_S at 8–16K context would be borderline on this budget. The KV cache is only 0.25–0.5 GB, but there is compute-buffer overhead. With Q4_K_M, offloading about 3–6 of the 33 layers is likely needed. Expected decode on the laptop is about **25–45 tok/s fully on the GPU** (scaled by bandwidth from the 3070's 58 tok/s) and **about 12–25 tok/s with partial offload**. Prefill should be on the order of 1,000–1,500 tok/s, so 16K tokens of context means roughly 10–20 s to the first token. All of these are estimates and must be measured with `llama-bench`.
- Plan for Qwen3.5-4B Q4_K_M: fully on the GPU even at 32K. Estimated about 60–80 tok/s decode and 2,000+ tok/s prefill (unmeasured).
- Use text-only GGUFs (no mmproj) to save about 1.4 GB.
- KV quantization (q8_0) is barely needed for Qwen3.5 because the cache is tiny. It matters more for Gemma 3 or Phi-style full-attention models.
- In llama.cpp, MTP speculative decoding for Qwen3.5 (`--spec-type draft-mtp`) may speed up generation further. The gain on 6 GB is unmeasured.

### Gaps
- No measured tokens/s or VRAM for any model on an RTX 3060 Laptop 6 GB.
- KV-cache sizes for Qwen3.5-4B, Gemma 4 E4B and Gemma 4 12B were not measured.
- AWQ/EXL3 sizes were not researched. Those formats are mostly relevant to ExLlama or vLLM (section 5).

## 5. Runtimes on native Windows 11 and the simplest robust choice for a Python project

### Takeaway
The simplest robust choice is **llama.cpp's `llama-server`** from the official prebuilt Windows CUDA zip, called over its OpenAI-compatible HTTP API with the `openai` Python client. It needs no compilation and does not tie the runtime to Python 3.14. **Ollama** is the more convenient alternative, with the same OpenAI-compatible API, but it sets context length through a Modelfile. **llama-cpp-python** has no Python 3.14 CUDA wheels, so avoid it in-process. **vLLM** has no official native Windows support, and its community fork targets Python 3.12.

### Cited Findings
- llama.cpp: v1.0.0 was marked "Latest" on Nov 13 (year omitted on the page; inferred as 2026) and pre-release b12374 on Nov 14. Windows assets include `win-cuda-12.4-x64` and `win-cuda-13.5-x64` (with separate cudart DLL zips), plus Vulkan, CPU and other backends. MTP / NextN speculative decoding is in active development — [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases).
- Ollama exposes an OpenAI-compatible API at `http://localhost:11434/v1/` covering chat completions (streaming, JSON mode, tools, thinking control), the Responses API (from v0.13.3) and embeddings. Context size cannot be set via the OpenAI API; use a Modelfile `PARAMETER num_ctx <n>`. Thinking is turned off with `reasoning_effort: "none"` for boolean-thinking models — [Ollama docs](https://docs.ollama.com/api/openai-compatibility).
- llama-cpp-python has no workflow building 3.14 wheels, and community Windows CUDA wheels cover Python 3.10–3.13 (for example 0.3.20) — [llama-cpp-python issue #2136](https://github.com/abetlen/llama-cpp-python/issues/2136); [dougeeai wheels](https://github.com/dougeeai/llama-cpp-python-wheels/). Building from source needs VS 2022 and the CUDA Toolkit — [Medium guide](https://medium.com/@eddieoffermann/llama-cpp-python-with-cuda-support-on-windows-11-51a4dd295b25).
- vLLM has had no official Windows support as of May 2026. The SystemPanic/vllm-windows fork v0.20.0 (Apr 30 2026) ships wheels for Python 3.12 + CUDA 13 + PyTorch 2.11 and lacks FlashInfer and FA3/4. Docker Model Runner's vLLM backend on Windows runs through WSL2 — [fazm.ai](https://fazm.ai/t/vllm-windows-support-2026); [hackernoon](https://hackernoon.com/how-to-run-vllm-natively-on-windows); [dasroot](https://dasroot.net/posts/2026/05/run-vllm-natively-windows-without-wsl/).
- LM Studio carries the Qwen3.6 models in its catalog — [LM Studio](https://lmstudio.ai/models/qwen3.6).

### Inferences
- The project's torch build is 2.14.1+cu130 on Python 3.14. A `llama-server` sidecar keeps the LLM runtime out of the Python environment, which avoids wheel and CUDA conflicts. It also matches the existing DeepSeek integration, which already uses an OpenAI-style API, so switching between remote and local generation could be just a change of base URL and model. Unloading the model to free VRAM for the embedder or reranker means stopping the server process, or using Ollama's `keep_alive: 0`. The Ollama behavior is from training knowledge and was not verified this session.
- On CUDA builds: the driver reports CUDA 13.0. The `cuda-12.4` llama.cpp build is the safe choice, since a newer driver runs older CUDA 12 runtimes. The `cuda-13.5` build depends on CUDA minor-version compatibility with a 13.0 driver, which was not verified here, so test it before relying on it.
- transformers + bitsandbytes 4-bit on 6 GB would be slower than llama.cpp, and its KV-cache handling is less memory-efficient. ExLlamaV2/V3 on native Windows needs matching torch/CUDA wheels. Neither was verified for Python 3.14 / torch 2.14 this session, so both should be treated as higher-risk options.

### Gaps
- No 2026 source was found on ExLlamaV3 Windows wheels or on bitsandbytes with Python 3.14 + cu130.
- SGLang Windows status was not researched. It is assumed to be Linux/WSL only, which is unverified.
- Ollama's Qwen3.5 support details and whether its default context fits 6 GB were not verified.

## 6. Reasoning ("thinking") modes: do they help RAG answers or just cost tokens on this hardware?

### Takeaway
On this hardware, thinking should be **off by default** for RAG answer generation. Qwen3.5 small models are very verbose when thinking, and no 2026 evidence was found that thinking improves faithfulness to the provided context. Some evidence suggests reasoning traces can themselves be unfaithful. A thinking toggle could be kept for multi-hop questions.

### Cited Findings
- Qwen3.5 thinking is ON by default. Disable it with `chat_template_kwargs: {"enable_thinking": false}`; the `/think` and `/nothink` soft switches are not supported. Recommended non-thinking sampling: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B).
- Token cost: to run the AA Intelligence Index, Qwen3.5-4B used about 240M output tokens and the 9B about 260M, versus 98M for Qwen3.5-27B and 57–69M for frontier closed models. The small models are 2.5–4× more verbose than larger ones — [Artificial Analysis](https://artificialanalysis.ai/articles/qwen3-5-small-models). The 9B Intelligence Index is 32.4 with reasoning vs 27.3 without — [localllm.in](https://localllm.in/blog/best-local-llms-8gb-vram-2025).
- In open-book QA, faithfulness hallucinations are more pronounced in chain-of-thought than in final answers — [OpenReview preprint](https://openreview.net/pdf/5d2200d660461b23802648abe0dbd119a5d99617.pdf). In RAG, retrieval-augmented reasoning raised confidence in biased outputs (PAKDD 2026) — [arXiv 2602.09442](https://arxiv.org/html/2602.09442). Explicit rationale generation improved accuracy over vanilla RAG on BioASQ and PubMedQA — [alphaXiv 2603.10143](https://www.alphaxiv.org/abs/2603.10143).
- Vectara's thinking variant qwen3-next-80b-a3b-thinking shows 9.3% hallucination, versus 4.8% for Qwen3-8B. Different models, so this is only indicative — [Vectara](https://github.com/vectara/hallucination-leaderboard).
- Gemma 4: thinking is opt-in (`<|think|>`). E2B/E4B do not emit an empty thought block when thinking is off — [HF gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it).

### Inferences
- At an estimated 25–45 tok/s, 500–2,000 thinking tokens add about 15–80 s per answer. That is a large latency cost for a likely small faithfulness gain.
- Thinking could help multi-hop synthesis across chunks. Run an A/B test on the project's own eval set rather than enabling it by default.

### Gaps
- No direct thinking-on vs thinking-off ablation on faithfulness metrics (FaithEval, RAGAS) was found for Qwen3.5 or Gemma 4.

## 7. Licenses (public open-source repository)

### Takeaway
All the top candidates are permissive: Qwen3.5 small, Qwen3.6, Qwen3.8-27B, Gemma 4 and Granite 4.1 are Apache 2.0, and Phi-4-mini is MIT. Licenses to avoid or check: LFM Open License (revenue cap), Qwen Community 1.0 / custom Qwen3.8 large-model licenses, and Falcon's TII license. The project's repository would only reference model IDs and download scripts, not redistribute weights.

### Cited Findings
- Qwen3.5-9B is Apache-2.0 — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B). Qwen3.6-35B-A3B and Qwen3.8-27B are Apache 2.0. Qwen3.8-Flash-Next uses Qwen Community 1.0. Qwen3.8-2.4T requires a commercial license above US$50M revenue — [Wikipedia: Qwen](https://en.wikipedia.org/wiki/Qwen).
- Gemma 4 is Apache 2.0, the first Gemma under it — [the-decoder](https://the-decoder.com/googles-gemma-4-is-now-available-with-apache-2-0-licensing-for-the-first-time/); [HF gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it).
- Granite 4.1 is Apache 2.0 — [HF blog Granite 4.1](https://huggingface.co/blog/ibm-granite/granite-4-1).
- Phi-4-mini is MIT. LFM2.5 uses the LFM Open License v1.0 (revenue cap). Falcon 3 uses the TII Falcon-LLM 2.0 license — [computingforgeeks](https://computingforgeeks.com/open-source-llm-comparison/).
- llama.cpp is MIT. Ollama is open source — [Wikipedia: Ollama](https://en.wikipedia.org/wiki/Ollama). The llama.cpp license is from training knowledge, not re-verified.

### Inferences
- Apache 2.0 weights pose no barrier to a public repository. The repository should record the model ID, license and quantizer (for example the GGUF provider) in its docs.

### Gaps
- Licenses of the GGUF re-uploads (bartowski, Unsloth) usually inherit the base license. This was not checked per repository.

## 8. Ranked recommendation for this hardware

### Takeaway
1. **Best quality that fits: Qwen3.5-9B Instruct, text-only GGUF, IQ4_XS or Q4_K_S (Q4_K_M with about 3–6 layers on the CPU if it does not fit), thinking off, 16K context, served by `llama-server` (llama.cpp CUDA build).**
2. **Faster fallback: Qwen3.5-4B Instruct Q4_K_M (about 2.7 GB), fully on the GPU, 32K context, thinking off.**
3. Worth an A/B test for Russian fluency: Gemma 4 E4B (QAT / Q4) as an alternative fallback.
4. Not recommended as the primary choice: Granite 4.1 (no Russian), Phi-4-mini and Ministral 3 (high Vectara hallucination), Qwen3.6-35B-A3B and Gemma 4 26B-A4B (do not fit in 6 GB VRAM plus 16 GB RAM at a sane quant), Gemma 4 12B (about 7+ GB at Q4 needs offload with a full-attention-style cache; not measured).

### Cited Findings
- Qwen3.5-9B leads the small class on the Intelligence Index (32 vs 27 for the 4B and 18 for Qwen3 4B), MMMLU 81.2, IFEval 91.5 and AA-LCR 63.0. KV cache is 0.5 GB at 16K — [Artificial Analysis](https://artificialanalysis.ai/articles/qwen3-5-small-models); [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B); [localllm.in](https://localllm.in/blog/best-local-llms-8gb-vram-2025).
- Practitioner 6 GB guides (2026) name Qwen3.5-4B Q4_K_M as the best fully fitting 6 GB model, and say 9B "consumes the whole budget" — [runaihome](https://runaihome.com/blog/best-local-llm-6gb-vram-2026/); [promptquorum](https://www.promptquorum.com/prompt-bites/best-local-llm-6gb-vram).
- Vectara grounded-hallucination results for the predecessors: Qwen3-8B 4.8% and Qwen3-4B 5.7%, versus Phi-4-mini 23.5% and Ministral-3-8b-2512 21.7% — [Vectara](https://github.com/vectara/hallucination-leaderboard).

### Inferences
- The ranking rests on vendor and general benchmarks plus RAG results for the previous Qwen3 generation. Qwen3.5's RAG faithfulness and Russian quality are unmeasured. Before committing, the project should run a small local eval with 20–50 questions: answerable vs unanswerable, English chunks with Russian answers, and a citation-format check. Candidates are Qwen3.5-9B, Qwen3.5-4B and Gemma 4 E4B, each with thinking off. Measure with `llama-bench` and record prefill and decode tokens/s at 8K and 16K on the actual laptop.
- Compared with the DeepSeek API, any of these local models is likely to be noticeably weaker in Russian answer quality and synthesis across many chunks. That is reasoning from the scale gap, not measured.

### Gaps
- No direct head-to-head of these candidates on a RAG task in Russian.
- No measured performance on the target GPU.
