# Query translation (any language → English) before retrieval: model choice for a 6 GB VRAM laptop (as of 2026-11-14)

Scope note: research only. Nothing was downloaded or installed. Research date: 2026-11-14. The step being evaluated translates a short user search query (5–60 words, mostly Russian or Slovak, sometimes other languages) into English before retrieval over mostly English scientific articles and books. Scientific and psychological terms must map to the established English term ("лимеренция" → "limerence", "тревожный тип привязанности" → "anxious attachment style"). The step outputs only the English query, optionally with 1–2 alternative phrasings, and passes English queries through unchanged. Hardware: RTX 3060 Laptop 6 GB, 16 GB RAM, Windows 11 native, Python 3.14.10, torch 2.14.1+cu130, transformers 5.23.0. A `llama-server` sidecar (llama.cpp, Windows CUDA build) is planned for local generation with Qwen3.5-9B IQ4_XS, and only one model is in VRAM at a time.

Labels used below: **Verified** means read on a primary source (model card, HF API, license file, paper, PyPI) this session. **Reported** means a secondary source or a vendor claim not independently checked. **Inference** means my own reasoning or estimate. Treat inferences as hypotheses to measure.

## 1. Short answer

- **Default local translator: Qwen3.5-4B (Instruct, thinking off), GGUF, served by the same `llama-server`.** Apache-2.0, 201 languages including Slovak and Russian, and the only candidate that does everything this step needs well. It knows established terminology from general pretraining, follows an instruction to pass English through, and can emit alternative phrasings as JSON. Download: `unsloth/Qwen3.5-4B-GGUF`, file `Qwen3.5-4B-Q4_K_M.gguf` (2.74 GB) or `Qwen3.5-4B-IQ4_XS.gguf` (2.48 GB). The source model is `Qwen/Qwen3.5-4B`.
- **Best dedicated MT model, as a challenger to test: `tencent/Hy-MT2-1.8B-GGUF`** (`Hy-MT2-1.8B-Q8_0.gguf`, 1.91 GB, Apache-2.0, May 2026). It is half the size, translation-specialized, and has a terminology-hint prompt. It is not the default because **Slovak is not in its supported-language list**.
- **The cloud API is better on quality and essentially free at this volume** (about $0.04–0.06 per 1,000 queries at budget prices). Whenever the pipeline already sends the query to the cloud for answer generation, it is the better choice for this step too. Keep a local default for offline or local-only mode.
- **Exclude** NLLB-200 and SeamlessM4T (CC-BY-NC), Tower+ (CC-BY-NC-SA), and Hunyuan-MT-7B, Hunyuan-MT-Chimera-7B and HY-MT1.5 (their license excludes the EU, and this project is developed in the EU).

## 2. Candidates: facts per model

### 2.1 Dedicated translation models

| Model (HF repo) | Date | License | ru / sk | Size | Notes |
|---|---|---|---|---|---|
| **Hy-MT2-1.8B / 7B / 30B-A3B** (`tencent/Hy-MT2-1.8B`, `tencent/Hy-MT2-7B`; GGUF `tencent/Hy-MT2-1.8B-GGUF`, `tencent/Hy-MT2-7B-GGUF`) | 2026-05-21 | **Apache-2.0** (verified in LICENSE.txt) | ru yes, **sk no** (cs yes) | 1.8B GGUF: Q4_K_M 1.13 GB, Q6_K 1.47 GB, Q8_0 1.91 GB. 7B GGUF: Q4_K_M 4.62 GB, Q6_K 6.16 GB, Q8_0 7.98 GB | Strongest open MT family found. Has a terminology-intervention prompt. No system prompt. |
| **TranslateGemma 4B / 12B / 27B** (`google/translategemma-4b-it`) | 2026-01-15 (paper 2026-01-13) | Gemma Terms of Use; upstream repo **gated** (manual) | ru both directions; **sk trained en→sk only** | BF16 8.6 GB; community GGUF Q4_K_M 2.49 GB, Q8_0 4.13 GB | Gemma 3 based. Needs the source language code in the prompt. About 2K-token context. |
| HY-MT1.5-1.8B / 7B, Hunyuan-MT-7B, Hunyuan-MT-Chimera-7B (`tencent/...`) | 2025-08 / 2025-12 | Tencent Hunyuan Community License, **"DOES NOT APPLY IN THE EUROPEAN UNION"** (verified in License.txt) | ru yes, sk no | 7B | Excluded on license grounds. |
| Seed-X-PPO-7B (`ByteDance-Seed/Seed-X-PPO-7B`) | 2025-07 | OpenMDW (permissive) | ru yes, **sk no** | ~8B BF16 | No chat template. Needs a language tag such as `<en>` at the end of the prompt. |
| Opus-MT / Marian (`Helsinki-NLP/opus-mt-ru-en`, `opus-mt-sk-en`, `opus-mt-tc-big-zle-en`, `opus-mt-tc-big-zlw-en`, `opus-mt-mul-en`) | 2020–2023 | ru-en CC-BY-4.0; sk-en Apache-2.0; tc-big-* CC-BY-4.0; mul-en Apache-2.0 | one model per pair or language group | ru-en 0.31 GB, sk-en 0.30 GB, tc-big-zlw-en 0.47 GB | Tiny and fast on CPU, but older and weak on rare terms. |
| MADLAD-400-3B-MT (`google/madlad400-3b-mt`) | 2023-11 | Apache-2.0 | yes | 11.76 GB fp32 safetensors (~3B, T5) | Uses a `<2en>` prefix. Ranked below DeepL, Google Translate and GPT-4o on Slovak in skLEP. |
| NLLB-200 (`facebook/nllb-200-distilled-600M`), SeamlessM4T v2 (`facebook/seamless-m4t-v2-large`) | 2022 / 2023 | **CC-BY-NC-4.0** | yes | 0.6B+ | Non-commercial, so excluded as a default. |
| Tower+ 2B / 9B (`Unbabel/Tower-Plus-2B`) | 2025-06 | **CC-BY-NC-SA-4.0** | sk not confirmed | 2.6B / 9B | Excluded. |
| ALMA-7B-R (`haoranxu/ALMA-7B-R`) | 2024-01 | MIT | ru yes, sk no | 7B | Llama-2 era, outdated. |
| SalamandraTA 2B / 7B (`BSC-LT/...`) | 2025 | conflicting: 2B card says Apache-2.0 (reported); the 7B GGUF repo is tagged **GPL-3.0** on the HF API; the WMT25 7B is research-only | sk yes | 2B / 7B | License situation unclear. Not recommended without checking. |
| EuroLLM-1.7B-Instruct / 9B-Instruct-2512 (`utter-project/...`) | 2024 / 2026-01 | Apache-2.0 | all EU languages incl. sk | 1.7B / 9B | General LLM with translation focus. No 2026 terminology evidence found. |

Cited findings:
- Hy-MT2 release 2026-05-21, sizes 1.8B / 7B / 30B-A3B, Apache-2.0, 33 languages (the card's table has 38 entries). The language list includes Russian and Czech but **not Slovak**. Recommended sampling for 1.8B and 7B: temperature 0.7, top_p 0.6, top_k 20, repetition_penalty 1.05. The default English prompt: "Translate the following text into {target_lang}. Note that you should only output the translated result without any additional explanation:\n\n{source_text}". A terminology variant prepends "Reference the following translations: X translates to Y …". Requires transformers ≥ 5.6.0 for the HF weights — [HF tencent/Hy-MT2-7B](https://huggingface.co/tencent/Hy-MT2-7B), [HF tencent/Hy-MT2-1.8B-GGUF](https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF) (verified).
- Hy-MT2 tech report, Table 2 (XCOMET-XXL / CometKiwi / GEMBA ×100), FLORES-200 EN⇔XX: Hy-MT2-1.8B 90.00 / 85.46 / 84.05; Hy-MT2-7B 93.52 / 88.07 / 89.34; HY-MT1.5-7B 90.93 / 86.50 / 85.66; Qwen3.6-35B-A3B 90.87 / 86.52 / 88.77; Gemini 3.1 Pro (thinking) 94.42 / 88.38 / 92.68. These are aggregates only, with no per-language (ru→en) numbers. This is a vendor paper, not independent — [arXiv 2605.22064v2](https://arxiv.org/html/2605.22064v2) (verified, 2026-05-25).
- IFMTBench (translation instruction-following, from the Tencent team): Hy-MT2-1.8B 69.36 overall vs Qwen3.5-4B 66.65. Qwen3.5-4B is slightly better on general instruction following (81.15 vs 80.22) — [arXiv 2605.28218](https://arxiv.org/pdf/2605.28218) (reported via search summary; not read in full).
- The Hy-MT2 GGUF READMEs say "This gguf depends on our STQ kernel … PR #22836". PR #22836 adds an STQ1_0 ternary (~1.31 bpw) CPU/ARM-NEON quant for the 1.25-bit Hy-MT model. It was **open, not merged**, when checked, and it has no CUDA kernel — [llama.cpp PR #22836](https://github.com/ggml-org/llama.cpp/pull/22836) (verified). Mainline llama.cpp has a `hunyuan-dense` architecture (PR #14878, 2025) (reported via mirror).
- TranslateGemma: 4B / 12B / 27B, Gemma 3 based, 55 languages. WMT24++ (55 pairs, **all en→xx**) MetricX↓ / COMET22↑: 4B 5.32 / 80.1 (Gemma 3 4B base: 6.97 / 77.2), 12B 3.60 / 83.5, 27B 3.09 / 84.4. **Slovak appears only as en→sk in the SFT data; Russian is in both directions.** Human MQM showed a Japanese→English regression caused by named-entity mistranslations — [HF paper page 2601.09012](https://huggingface.co/papers/2601.09012), [HF google/translategemma-4b-it](https://huggingface.co/google/translategemma-4b-it) (verified).
- The TranslateGemma prompt is a single user turn with a fixed persona text: "You are a professional {SOURCE_LANG} ({SOURCE_CODE}) to {TARGET_LANG} ({TARGET_CODE}) translator. …", then "Produce only the {TARGET_LANG} translation …", two blank lines, and the text. The official template uses structured content (`source_lang_code`, `target_lang_code`), which ordinary OpenAI-style clients cannot produce — [Ollama translategemma](https://ollama.com/library/translategemma:latest), [42ailab GGUF card](https://huggingface.co/42ailab/TranslateGemma-4B-GGUF) (verified).
- No bartowski or unsloth TranslateGemma GGUF exists (HF API returned not-found). Ungated community GGUFs exist: `bullerwins/translategemma-4b-it-GGUF` and `mradermacher/translategemma-4b-it-GGUF` (Q4_K_M 2.49 GB, IQ4_XS 2.28 GB, Q8_0 4.13 GB) (verified via HF API). No Gemma 4-based TranslateGemma from Google was found.
- Hunyuan-MT-7B and HY-MT1.5-7B License.txt: "THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA" — [HF tencent/Hunyuan-MT-7B](https://huggingface.co/tencent/Hunyuan-MT-7B), [HF tencent/HY-MT1.5-7B](https://huggingface.co/tencent/HY-MT1.5-7B) (verified).
- Seed-X-PPO-7B: 28 languages (ru, cs; **no sk**), OpenMDW, paper 2025-07-18, prompt needs a trailing language tag — [HF ByteDance-Seed/Seed-X-PPO-7B](https://huggingface.co/ByteDance-Seed/Seed-X-PPO-7B) (verified).
- Opus-MT ru-en BLEU: newstest2019 31.4, Tatoeba 61.1. A third-party CT2 conversion reports 35.5 BLEU on FLORES+ ru→en. sk-en: 42.2 BLEU on JW300 (not a news or science domain) — [HF opus-mt-ru-en](https://huggingface.co/Helsinki-NLP/opus-mt-ru-en), [HF opus-mt-sk-en](https://huggingface.co/Helsinki-NLP/opus-mt-sk-en), [murmur-translation-ct2](https://huggingface.co/beshkenadze/murmur-translation-ct2) (reported). Licenses and sizes verified via HF API. `opus-mt-ru-en` and `opus-mt-sk-en` ship only `pytorch_model.bin` (pickle), with no safetensors.
- skLEP: a comparison of translation systems on 90 Slovak sentences ranked DeepL, Google Translate and GPT-4o above MADLAD-400-3B and NLLB-3.3B — [arXiv 2506.21508](https://arxiv.org/pdf/2506.21508) (reported).
- Licenses for MADLAD (Apache-2.0), NLLB and SeamlessM4T v2 (CC-BY-NC-4.0), Tower+ (CC-BY-NC-SA-4.0), ALMA-R (MIT), Seed-X ("other" = OpenMDW), the SalamandraTA-7B GGUF (GPL-3.0 tag) and EuroLLM (Apache-2.0) were verified via the HF API tags on 2026-11-14.

### 2.2 Small general LLMs as translators

| Model | License | Translation evidence | GGUF size (Q4_K_M / IQ4_XS) | Notes |
|---|---|---|---|---|
| **Qwen3.5-4B** (`Qwen/Qwen3.5-4B`) | Apache-2.0 | WMT24++ **66.6** (9B: 72.6) | unsloth 2.74 / 2.48 GB; bartowski 3.01 / 2.67 GB | 201 languages. Thinking is ON by default. |
| Qwen3.5-2B | Apache-2.0 | WMT24++ 45.8 (thinking) | bartowski 1.40 / 1.26 GB | Big quality drop vs 4B. Non-thinking by default. |
| Qwen3.5-0.8B | Apache-2.0 | WMT24++ 27.2 (thinking) | <1 GB | Too weak. |
| Gemma 4 E4B / E2B (`google/gemma-4-E4B-it`) | Apache-2.0 | No WMT number on the card; MMMLU 76.6 / 67.4 | E4B 4.98 / 4.72 GB; E2B 3.11 / 2.98 GB | The Per-Layer-Embedding parameters make the GGUFs large for their quality class. |
| Qwen3.5-9B (planned generator) | Apache-2.0 | WMT24++ 72.6 | IQ4_XS 5.50 GB | Best local quality, but loading it just to translate costs a full 9B load. |

Cited findings:
- Qwen3.5-4B / 9B multilingual rows: WMT24++ 66.6 / 72.6, MMMLU 76.1 / 81.2, MMLU-ProX 71.5 / 76.3. Thinking mode is on by default. Disable it with `chat_template_kwargs: {"enable_thinking": false}`. Non-thinking sampling: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 — [HF Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) (verified). The card does not state which metric "WMT24++" uses, so these numbers compare only within the Qwen card.
- Qwen3.5-2B WMT24++ 45.8 and 0.8B 27.2 (thinking mode). "Qwen3.5-2B operates in non-thinking mode by default" — [HF Qwen/Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) (verified).
- Gemma 4 E4B: 4.5B effective / 8B total parameters. MMMLU 76.6% (E2B 67.4%). No WMT24++ on the card. Disable thinking by omitting `<|think|>` / `enable_thinking=False` — [HF google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it) (verified).
- GGUF file sizes listed above were verified via the HF API (`unsloth/Qwen3.5-4B-GGUF`, `bartowski/Qwen_Qwen3.5-4B-GGUF`, `bartowski/Qwen_Qwen3.5-2B-GGUF`, `unsloth/gemma-4-E4B-it-GGUF`, `unsloth/gemma-4-E2B-it-GGUF`).
- A Tencent-team paper using a translation-instruction benchmark puts Hy-MT2-1.8B (69.36) slightly above Qwen3.5-4B (66.65) — see 2.1. No independent head-to-head of TranslateGemma-4B, Hy-MT2-1.8B and Qwen3.5-4B was found.

### 2.3 Cloud API for this step

- Budget prices (from the sibling note `api_llm.md`, verified there on 2026-11-14): GPT-6 Luna and Claude Haiku 5.5 at $0.10 / $0.50 per M tokens; Gemini 2.5 Flash-Lite at $0.10 / $0.40; DeepSeek V4.1 Flash at $0.30 / $1.20.
- Hy-MT2-7B is on OpenRouter (provider: Tencent Cloud) at $0.074 input / $0.295 output per M tokens — [OpenRouter tencent/hy-mt2-7b](https://openrouter.ai/tencent/hy-mt2-7b) (verified).
- Cost (inference): one translation call is about 250 input tokens (instructions, few-shot examples, query) and about 80 output tokens. At $0.10 / $0.40 that is about $0.00006 per query, roughly **$0.06 per 1,000 queries**, which is negligible next to answer generation (about $1–9 per 1,000 queries in `api_llm.md`).
- Quality (inference): frontier-class cloud models top the Russian Arena and know rare scientific terms better than any 2–4B local model. Gemini 3.1 Pro leads Hy-MT2 on FLORES EN⇔XX in Tencent's own table. Network round-trip latency is about 0.5–1.5 s, comparable to a cold local load.
- Privacy and availability: if the answer is generated in the cloud anyway, the query leaves the machine regardless, so cloud translation adds no new exposure. In local-only or offline mode it is unavailable.

## 3. Runtime on native Windows, Python 3.14

- **llama.cpp `llama-server` (recommended for every GGUF candidate).** It keeps the translator out of the Python environment, the same as the planned generator. Router mode (since 2025-12-11) runs `llama-server` without `-m`, loads a model on first request, evicts the least-recently-used one (`--models-max`, default 4), and exposes `POST /models/load` and `POST /models/unload`. A `--models-preset config.ini` file gives per-model settings — [HF blog: Model management in llama.cpp](https://huggingface.co/blog/ggml-org/model-management-in-llamacpp) (verified). Whether `-ngl` can be set per model in a preset is not documented. The server has `--chat-template-kwargs`, `--reasoning on|off|auto` and `--reasoning-budget` — [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) (verified). The README documents `json_schema` on `/completion`; `response_format` on `/v1/chat/completions` is listed only as a feature.
- Windows CUDA builds (from `local_llm.md`): `win-cuda-12.4-x64` is the safe build for a 13.0 driver; `win-cuda-13.5-x64` relies on minor-version compatibility and should be tested.
- **transformers path** (TranslateGemma, Hy-MT2 HF weights, Opus-MT, MADLAD): works in principle with transformers 5.23 / torch 2.14. Hy-MT2 needs transformers ≥ 5.6 and `trust_remote_code=True`. The "translation" pipeline no longer exists in transformers v5 (Hy-MT2 card). A 4B model in BF16 (8.6–9.3 GB) does not fit in 6 GB, so it would need bitsandbytes. No source confirms bitsandbytes on Python 3.14 + cu130 (see `local_llm.md`).
- **Opus-MT on Python 3.14:** `sentencepiece` 0.2.3 (2026-11-05) ships `cp314-win_amd64` wheels, and `ctranslate2` 4.9.0 (2026-11-10) ships `cp314-win_amd64` wheels (verified via the PyPI JSON API). Marian models therefore run either through transformers or, faster on CPU, through CTranslate2 int8. Inference: loading pickle-only `pytorch_model.bin` in transformers 5 may need a local safetensors conversion; this was not verified.
- `llama-cpp-python` 0.3.36 (2026-10-01) has no Windows cp313 or cp314 wheels on PyPI (verified). This is another reason to use the prebuilt `llama-server` binary rather than in-process bindings.

## 4. Latency and load time on this laptop (estimates, not measurements)

There are no measured numbers for any of these models on an RTX 3060 Laptop 6 GB. The estimates below scale from `local_llm.md` (Qwen3.5-9B Q4_K_M at about 58 tok/s on a desktop RTX 3070, 386 GB/s; the laptop 3060 has about 336 GB/s) and assume an NVMe SSD. All of them are inference.

| Option | VRAM | Cold load (process start, weights read, CUDA init) | Translate one 30-word query (~60 output tokens incl. 2 alternatives) |
|---|---|---|---|
| Qwen3.5-4B Q4_K_M on GPU | ~3 GB | ~2–5 s | ~0.6–1.2 s (≈60–80 tok/s decode) |
| Hy-MT2-1.8B Q8_0 on GPU | ~2.2 GB | ~1.5–3 s | ~0.3–0.6 s (one translation only) |
| TranslateGemma-4B Q4_K_M on GPU | ~3 GB | ~2–5 s | ~0.4–0.8 s (one translation only) |
| Qwen3.5-9B IQ4_XS (already loaded) | ~5.5–6 GB | 0 if resident, otherwise ~4–8 s | ~1.5–2.5 s (25–45 tok/s) |
| Qwen3.5-4B Q4_K_M on CPU (`-ngl 0`) | 0 | ~1–3 s | ~4–8 s (≈8–15 tok/s) — too slow |
| Opus-MT via CTranslate2 int8 on CPU | 0 | <1 s | ~0.1–0.3 s |
| Cloud API | 0 | 0 | ~0.5–1.5 s network round trip |

Inference on pipeline placement (not a product decision): the translator runs first, before the embedder, reranker and generator. A ~3 GB translator can share the 6 GB card with a 0.6B embedder or reranker (about 1.2 GB each in BF16), but not with the 9B generator. If the 9B generator stays resident between queries, the cheapest local arrangement is to translate with the resident 9B and skip loading a separate translator. Which arrangement is best depends on the final load/unload sequence, which the main session owns.

## 5. Terminology, passthrough, alternatives: how each class fits the task

- **Terminology** (inference, supported by the cited sources): dedicated MT models are trained on parallel sentences and tend to translate rare terms literally or by morphology. The search found reports that domain terminology is where LLM-prompted translation beats standard MT — [ICML 2026 Indonesian–Arabic Fiqh CLIR case study](https://icml.cc/virtual/2026/80180) (reported). Hy-MT2 can take term hints ("X translates to Y"), which helps only if the project keeps a glossary. A general LLM can be asked directly for "the established English scientific term", and few-shot examples fix the format. None of the sources tested "лимеренция" or similar terms, so this must be checked with a small test set (see 7).
- **Passthrough of English queries:** an MT model asked to translate English into English usually copies it, but it can paraphrase, and TranslateGemma needs a source-language code. The project would therefore need a language detector in front. An LLM handles "if already English, return unchanged" by instruction.
- **Alternative phrasings:** only general LLMs produce these reliably. MT models output one translation.
- **"Any language":** TranslateGemma (55 languages) and Hy-MT2 (33) cover fixed lists. Qwen3.5 claims 201 languages and dialects. Opus-MT needs one model per source language or group.
- **Slovak:** Qwen3.5 (201 languages) and EuroLLM (all EU languages) list it. TranslateGemma trained only en→sk. Hy-MT2, Seed-X and ALMA do not list Slovak. Inference: Czech support may carry over to Slovak, but this is unverified. No 2026 sk→en benchmark of any of these models was found. The only number found is FLORES sk→en 29.83 for Llama-3.1-8B — [arXiv 2510.13580](https://arxiv.org/pdf/2510.13580) (reported).

## 6. Recommendation

### Default local translator
- **Model:** Qwen3.5-4B Instruct, thinking off.
  - Source repo: `Qwen/Qwen3.5-4B` (Apache-2.0).
  - GGUF repo: `unsloth/Qwen3.5-4B-GGUF`.
  - File: `Qwen3.5-4B-Q4_K_M.gguf`, **2.74 GB** download. If VRAM is tight next to an embedder, use `Qwen3.5-4B-IQ4_XS.gguf` (2.48 GB). The equivalent bartowski build is `bartowski/Qwen_Qwen3.5-4B-GGUF` / `Qwen_Qwen3.5-4B-Q4_K_M.gguf` (3.01 GB).
  - The vision projector (mmproj) is not needed.
- **Runtime:** the same prebuilt `llama-server` (Windows CUDA 12.4 build), router mode with a preset entry for the translator, called via `/v1/chat/completions` from the existing OpenAI-compatible client. Thinking is off: set `--reasoning off` or `--chat-template-kwargs "{\"enable_thinking\":false}"` on the preset, or pass `chat_template_kwargs` per request. Use a context of 2048 and `max_tokens` of about 160.
- **Why:** it is the only Apache-2.0 option that covers Russian, Slovak and "any language", handles terminology by instruction, passes English through, and returns alternatives. It is about half the size of the 9B generator and shares its tokenizer and template family, so prompting and parsing code stays the same. Its WMT24++ score (66.6) is clearly above Qwen3.5-2B (45.8). A dedicated MT model can beat it at translation proper (Hy-MT2-1.8B scores 69.36 vs 66.65 on Tencent's IFMTBench; no independent ru→en or sk→en comparison exists), but that matters less for short, terminology-heavy queries than Slovak coverage and instruction following.
- **Sampling** (inference, adapted for deterministic output): temperature 0–0.2, top_p 0.8, top_k 20, presence_penalty 0. Qwen's general non-thinking defaults (temperature 0.7, presence_penalty 1.5) are tuned for open-ended chat, not exact term mapping.
- **Prompt format** (proposed; to be validated on the test set):

  System:
  ```
  You convert search queries for an English-language scientific retrieval system.
  Rules:
  1. Translate the query into English. Use the established English scientific term
     (psychology, psychiatry, medicine, biology), never a literal or calqued translation.
  2. If the query is already in English, copy it unchanged into "query_en".
  3. Keep names, acronyms, citations, numbers and formulas as they are.
  4. Do not answer or explain the query.
  5. Give up to 2 alternative English phrasings useful for search (synonyms, the more
     common term, or the expanded acronym). Use [] if none are useful.
  Output only JSON: {"query_en": "...", "alternatives": ["...", "..."]}
  ```
  Few-shot turns (user → assistant), for example:
  - `лимеренция и тревожный тип привязанности` → `{"query_en": "limerence and anxious attachment style", "alternatives": ["limerence and anxious attachment", "romantic obsession and attachment anxiety"]}`
  - `hraničná porucha osobnosti a emočná dysregulácia` → `{"query_en": "borderline personality disorder and emotion dysregulation", "alternatives": ["BPD emotional dysregulation"]}`
  - `learned helplessness in depression` → `{"query_en": "learned helplessness in depression", "alternatives": []}`

  Then the real query as the final user turn. Constrain the output with a JSON schema: `json_schema` on `/completion` is documented; `response_format` on the chat endpoint is listed but not documented. Parse defensively, and on failure fall back to the raw query.

### Challenger to A/B test locally
- `tencent/Hy-MT2-1.8B-GGUF` / `Hy-MT2-1.8B-Q8_0.gguf` (1.91 GB, Apache-2.0).
  - Prompt: one user turn, no system prompt. Text: "Translate the following text into English. Note that you should only output the translated result without any additional explanation:\n\n{query}". Optionally prepend glossary hints in the documented "X translates to Y" form.
  - Sampling: the vendor's settings (temperature 0.7, top_p 0.6, top_k 20, repetition_penalty 1.05), or greedy for determinism.
  - Runtime: `llama-server`. It must be confirmed that the standard Q8_0 / Q4_K_M files load in a mainline Windows CUDA build, because the README's STQ note refers to an unmerged PR (see 7).
- Use it if Russian terminology accuracy beats Qwen3.5-4B. Slovak queries would then need routing to Qwen or the cloud.

### Cloud API
- **Better and cheaper per query than any extra local load**, at about $0.06 per 1,000 queries with a budget model such as Gemini 2.5 Flash-Lite or GPT-6 Luna, using the same prompt and JSON output. Use it whenever the answer is generated in the cloud anyway. Keep Qwen3.5-4B as the default for local-only or offline mode.
- Choosing the specific cloud model belongs with the `api_llm.md` decision. `tencent/hy-mt2-7b` on OpenRouter ($0.074 / $0.295) is a cheap MT-specialised alternative, but it inherits the Slovak gap.

### Not recommended
- TranslateGemma-4B: Slovak is trained only en→sk; it needs a source-language code (so a language detector); it emits no alternatives; its official template is awkward through an OpenAI-style API; and the upstream repo is gated, which complicates "download the default model" for users of a public repository.
- Opus-MT: a reasonable CPU-only emergency fallback (Apache or CC-BY-4.0; CC-BY needs attribution), but it needs one model per language and is weak on rare terms.
- MADLAD-400-3B: 11.8 GB fp32, no terminology steering, and it ranked below commercial MT on Slovak.
- NLLB, SeamlessM4T and Tower+: non-commercial licenses.
- Hunyuan-MT and HY-MT1.5: license excludes the EU.

## 7. Open uncertainties and what to measure

1. **No ru→en or sk→en scores for the 2026 small models.** WMT24++ is en→xx only, and the Hy-MT2 and Qwen tables are aggregates. Build a 30–50 query test set (Russian, Slovak, English, plus a few other languages) with gold English terms. Score exact-term hits, passthrough correctness and JSON validity for Qwen3.5-4B, Hy-MT2-1.8B, Qwen3.5-9B and one cloud model. Better still, measure retrieval recall@k for original-only vs translated vs original+translated queries.
2. **Whether translation is needed at all.** The embedding note recommends a multilingual cross-lingual embedder. If the embedder handles Russian and Slovak queries well, translation may help mainly the lexical or BM25 side and terminology. Fusing the original and translated queries is an option to evaluate.
3. **Hy-MT2 GGUF on mainline llama.cpp (Windows CUDA).** The README says it depends on unmerged PR #22836 (STQ1_0, ARM-only). Inference: this likely applies only to the 1.25-bit file, since the Q4_K_M and Q8_0 files use standard quant types and the `hunyuan-dense` architecture is in mainline. Very high download counts (1.16M for the 7B GGUF) suggest it runs in common tools, but this was not verified.
4. **Load and latency numbers** in section 4 are estimates. Measure with `llama-bench` and wall-clock timing of `POST /models/load` on the laptop.
5. **Qwen's "WMT24++" metric** is undocumented on the card, so 66.6 vs 72.6 compares only within the Qwen family.
6. **Chat-endpoint JSON schema and per-request `chat_template_kwargs`** in the current `llama-server` are not documented in the README. Test them, or use `/completion` with `json_schema`.
7. **Release-date conflict for Hy-MT2-7B:** Tencent says 2026-05-21; OpenRouter lists 2026-08-19 (probably its own listing date).
