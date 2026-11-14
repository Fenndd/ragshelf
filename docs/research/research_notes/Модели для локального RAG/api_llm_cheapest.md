# Cheapest well-grounded hosted LLM for RAG answers (as of 2026-11-14)

This follows up on [api_llm.md](api_llm.md). The user rejected Gemini 3.8 Flash as the default and asked to "look at the current rating and choose the cheapest".

**Workload.** Each call carries 4k–16k tokens of retrieved English chunks plus the question. The model must answer faithfully from that context, cite chunks as `[n]`, and refuse when the context lacks the answer. Answers are often in Russian. The same model may also translate the user's query into English (about 50–200 tokens). One user in the EU, sequential queries.

**Cost formula.** Cost per 1,000 queries = 1,000 × (8,000 × input price + 800 × output price) / 1M. The `@16k` column uses 16,000 input tokens instead. These figures exclude reasoning tokens, caching, and OpenRouter's credit-purchase fee, which I did not verify.

**Method.** I read public pages and public JSON only: the OpenRouter model, endpoint, provider and ZDR listings, the Vectara GitHub repository and Hugging Face dataset metadata, and official pricing and deprecation pages. I made no sign-ups, paid calls or file downloads. Every number below was fetched on 2026-11-14 unless a snapshot date is given. **[V]** marks a verified fact, with its source. **[I]** marks my inference.

## 1. Rating snapshots used

| Rating | Snapshot date | What it measures | Access |
|---|---|---|---|
| Vectara HHEM-2.3 hallucination leaderboard | **2026-10-22** (README "Last updated on October 22, 2026"; latest commit 2026-10-22, merged 2026-10-23) | Hallucination rate when summarising a supplied document, and answer rate (how often the model does not refuse) | [GitHub README](https://github.com/vectara/hallucination-leaderboard) [V]; per-model JSON in [HF dataset vectara/results](https://huggingface.co/datasets/vectara/results), last modified 2026-10-23, matches the README [V] |
| Arena Text, Russian | **2026-11-11** (983,417 votes, 385 models) | Human chat preference in Russian | [arena.ai/leaderboard/text/russian](https://arena.ai/leaderboard/text/russian) [V]. The page renders only ranks 1–153 contiguously (row 154 is Claude Haiku 4.5 with its score hidden). Rank 153 = 1402. |
| RuQualBench | HF space last modified **2026-06-23** | Russian-language errors per 1,000 output tokens (critical / regular / minor) | [HF space kristaller486/RuQualBench](https://huggingface.co/spaces/kristaller486/RuQualBench) [V]; a community benchmark |
| FACTS Grounding (Kaggle) | not obtained | Grounded long-form answers | [Kaggle page](https://www.kaggle.com/benchmarks/google/facts-grounding) rendered only its title (JS). A third-party mirror ([benchmarklist](https://benchmarklist.com/benchmarks/facts_grounding/), 2026-05-06) has open models only and an unclear version, so I did not use it for decisions. |

Caveats on Vectara [I]:
- It is the best available proxy for "stays within the supplied context". It does not test `[n]` citation accuracy, English→Russian synthesis, or refusing when the answer is absent.
- Its "answer rate" means willingness to summarise, which is not RAG refusal.
- The README does not record the reasoning mode or the snapshot for DeepSeek-V4.1-Flash. The result file's model name is `deepseek-ai/DeepSeek-V4.1-Flash-`, which leaves open whether it was the 2026-09-10 or the 1017 snapshot.

## 2. Models that pass the grounding gate (Vectara ≤ ~5 % hallucination, ≥ 95 % answer rate)

From the 2026-10-22 README [V]:

| Model (Vectara row) | Halluc. | Answer rate | Hosted? |
|---|---:|---:|---|
| antgroup/finix_s1_32b | 1.8 % | 99.5 % | Not on OpenRouter (absent from `/api/v1/models`). I found no public API price, so it is excluded. |
| openai/gpt-5.4-nano-2026-03-17 | 3.1 % | 100 % | OpenAI, Azure, OpenRouter |
| google/gemini-2.5-flash-lite | 3.3 % | 99.5 % | Google AI Studio, OpenRouter |
| meta-llama/Llama-3.3-70B-Instruct-Turbo | 4.1 % | 99.5 % | OpenRouter (DeepInfra and others) |
| deepseek-ai/DeepSeek-V4.1-Flash | 4.2 % | 99.9 % | DeepSeek, OpenRouter (about 35 providers) |
| google/gemma-3-12b-it | 4.4 % | 97.4 % | OpenRouter (DeepInfra, NextBit) |
| mistralai/mistral-large-2411 | 4.5 % | 99.9 % | Not on OpenRouter (only 2407 and 2512 are listed). Excluded. |
| qwen/qwen3-8b | 4.8 % | 99.9 % | Not on OpenRouter. DashScope pricing not checked. Excluded. |
| *Borderline:* amazon/nova-2-lite, nova-pro, mistral-small-2501 | 5.1 % | 97.9–99.6 % | OpenRouter |
| *Borderline:* google/gemma-4-26b-a4b-it | 5.2 % | 99.8 % | OpenRouter, AI Studio (free only) |
| *Borderline:* qwen3-14b 5.4 %, nova-micro 5.5 %, gpt-5.4-mini 5.5 % | 5.4–5.5 % | ≥ 99.9 % | OpenRouter |

Excluded despite a low rate: Phi-4 (3.7 %, answer rate 80.7 %) and snowflake-arctic (4.3 %, 62.7 %).

Not on Vectara, so they can't be shown to pass:
- GPT-6 Luna and Claude Haiku 5.5 ($0.10/$0.50, which the earlier notes called the cheapest).
- Gemini 3.5 and 3.8 Flash and 3.5 Flash-Lite.

For calibration, newer and larger models do *worse* on Vectara: GPT-6 Sol 6.5 %, Gemini 3.1 Flash-Lite Preview 8.2 %, Claude Opus 5.5 9.9 %, Gemini 3 Flash Preview 13.5 % [V].

## 3. Cost table (sorted by cheapest compliant route; 8k in + 800 out)

Abbreviations:
- **OR** = OpenRouter (OpenAI-compatible `https://openrouter.ai/api/v1`).
- **ZDR** = the endpoint appears in OR's public list of zero-data-retention endpoints, [`/api/v1/endpoints/zdr`](https://openrouter.ai/api/v1/endpoints/zdr).

Prices come from [`/api/v1/models`](https://openrouter.ai/api/v1/models) and `/api/v1/models/{id}/endpoints`, fetched 2026-11-14, unless marked otherwise.

| # | Model / route | In / Out $ per 1M | **$ / 1k queries** | $ / 1k @16k | Halluc. / answer | Russian evidence | Deprecation | Data use (EU user) | OpenAI-compatible |
|---|---|---|---:|---:|---|---|---|---|---|
| 1 | **Gemma 4 26B A4B**: AI Studio `gemma-4-26b-a4b-it` free tier | free (paid tier "Not available") | **0.00** | 0.00 | 5.2 % / 99.8 % (borderline) | Arena-RU **#98, 1438** (895 votes); RuQualBench **#11** (0.45 normalised errors) | none listed | Free tier normally "used to improve", but the EEA clause applies paid terms to unpaid quota ([terms](https://aistudio.google.com/docs/terms), effective 2026-03-23) [V] | Gemini OpenAI-compat layer (not verified this session) |
| 2 | Gemma 4 26B A4B: OR `google/gemma-4-26b-a4b-it`, PrimeIntellect bf16 (ZDR) | 0.025–0.029 / 0.075–0.087 ¹ | **0.26–0.30** | 0.46–0.53 | same | same | none | ZDR [V] | yes (OR) |
| 3 | Amazon Nova Micro: OR `amazon/nova-micro-v1`, Bedrock eu-west-1 (ZDR) | 0.035 / 0.14 | 0.39 | 0.67 | 5.5 % / 100 % (fails ≤ 5) | none found | none seen | ZDR [V] | yes (OR) |
| 4 | Gemma 3 12B: OR `google/gemma-3-12b-it`, DeepInfra bf16 (ZDR; flex 0.04/0.12 = $0.42) | 0.05 / 0.15 | 0.52 | 0.92 | **4.4 % / 97.4 %** | **No direct evidence**: absent from Arena-RU ranks 1–153 (so ≤ 1402 or unrated); RuQualBench has only Gemma-3-27B (#18) | none seen; model is from 2025-03 | ZDR [V] | yes (OR) |
| 5 | Mistral Small 2501: OR `mistralai/mistral-small-24b-instruct-2501`, DeepInfra fp8 (ZDR) | 0.05 / 0.08 | 0.46 | 0.86 | 5.1 % / 97.9 % (borderline) | No direct evidence (RuQualBench has only Small 3.2, #22) | single provider; context 32k | ZDR [V] | yes (OR) |
| 6 | **DeepSeek V4.1 Flash 1017**: OR `deepseek/deepseek-v4.1-flash-1017`, cheapest ZDR endpoints | Particle AI flex 0.03/0.25 → **0.44**; Sail Research fp4 0.073/0.108 → **0.67**; Wafer mxfp4 0.038/0.50 → **0.70**; Particle AI us 0.06/0.50 → 0.88; PrimeIntellect 0.044/0.70 → 0.91; DeepInfra fp8 0.098/0.294 → **1.02** | **0.44–1.02** | 0.68–1.80 | **4.2 % / 99.9 %** | Arena-RU **#32, 1481** (the 2026-09-10 snapshot in "Max" thinking, 1,926 votes); RuQualBench predecessor "V4 Flash Instant" **#6** (0.34) | none announced; 1017 is DeepSeek's current `deepseek-flash` ([pricing](https://api-docs.deepseek.com/quick_start/pricing)) | ZDR endpoints [V] | yes (OR) |
| 7 | DeepSeek V4.1 Flash (2026-09-10): OR `deepseek/deepseek-v4.1-flash`, Baidu fp8 | 0.0507 / 0.2028 (OR shows `discount: 0.831`) | 0.57 | 0.97 | same | same | — | **Not ZDR**; Baidu headquartered in CN; promotional price [V] | yes (OR) |
| 8 | Gemini 2.5 Flash-Lite: AI Studio `gemini-2.5-flash-lite` (free tier exists for Standard; Flex/Batch paid 0.05/0.20 → $0.56) | 0.10 / 0.40 ([pricing](https://aistudio.google.com/docs/pricing)) | 1.12 (flex 0.56; free tier 0) | 1.92 | **3.3 % / 99.5 %** | **Weak**: absent from Arena-RU ranks 1–153; no RuQualBench row (its footer says Flash Lite results "may be overstated"); sibling Gemini 2.5 Flash is RuQualBench #12 | **not deprecated**, "remains available … until further notice" ([deprecations](https://aistudio.google.com/docs/deprecations)) [V] | Paid: prompts not used to improve products, logged "for a limited period". EEA: same terms on free quota [V]. Not ZDR on OR. | Gemini OpenAI-compat layer, or OR `google/gemini-2.5-flash-lite` (same price; AI Studio flex 0.05/0.20 also listed) |
| 9 | Llama 3.3 70B: OR `meta-llama/llama-3.3-70b-instruct`, DeepInfra turbo fp8 (ZDR) | 0.10 / 0.32 | 1.06 | 1.86 | 4.1 % / 99.5 % | No direct evidence (absent from Arena-RU ranks 1–153) | model from 2024-12 | ZDR [V] | yes (OR) |
| 10 | Qwen3-14B: OR `qwen/qwen3-14b`, DeepInfra fp8 (ZDR) | 0.12 / 0.24 | 1.15 | 2.11 | 5.4 % / 99.9 % | none | context 40,960 | ZDR [V] | yes (OR) |
| 11 | DeepSeek V4.1 Flash, direct `deepseek-flash` (also the OR "DeepSeek" endpoint at 0.15/0.60) | off-peak 0.15/0.60, peak 0.30/1.20 | 1.68 / 3.36 | 2.88 / 5.76 | 4.2 % / 99.9 % | as #6 | — | Data "collect[ed], process[ed] and store[d] … in People's Republic of China"; may be used to train, with an opt-out right ([privacy policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html), updated 2026-02-10) [V] | yes (`https://api.deepseek.com`) |
| 12 | GPT-5.4 nano: OpenAI `gpt-5.4-nano` (flex 0.10/0.625 → $1.30; Azure ZDR via OR $2.60) | 0.20 / 1.25 | 2.60 | 4.20 | **3.1 % / 100 %** | absent from Arena-RU ranks 1–153 | **Deprecated; shutdown 2027-04-01**, replacement `gpt-6-luna` ([deprecations](https://developers.openai.com/api/docs/deprecations), notice 2026-10-01) [V]. Fails the 6-month rule. | OpenAI API terms not re-fetched | yes |
| ref | GPT-6 Luna / Claude Haiku 5.5 (OR) | 0.10 / 0.50 (Luna OpenAI flex 0.05/0.25) | 1.20 (0.60) | 2.00 | **no Vectara row** | Luna (Max) Arena-RU #102, 1437; Haiku 5.5 not seen | none | Luna ZDR only via Azure; Haiku 5.5 ZDR via Vertex/Bedrock | yes |

¹ The two OpenRouter listings fetched minutes apart on 2026-11-14 show PrimeIntellect's Gemma 4 26B at 0.025/0.075 (models and endpoints API) and 0.029/0.087 (ZDR list).

Query translation (about 200 input + 100 output tokens) costs under $0.0001 per call on every row. It does not affect the ranking [I].

## 4. Reasoning (thinking) settings — verified defaults

- **DeepSeek V4.1 Flash.** Thinking is on by default with effort `high` [V]: OR `reasoning` object `default_enabled: true, default_effort: "high"`, supported efforts `max, high, low, none`; DeepSeek's [thinking-mode guide](https://api-docs.deepseek.com/guides/thinking_mode) says the same.
  - Turn it off on OR with `"reasoning": {"effort": "none"}` or `{"enabled": false}` ([OR reasoning docs](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)).
  - Turn it off on DeepSeek direct with `extra_body={"thinking": {"type": "disabled"}}`.
  - Reasoning tokens are billed as output [V].
- **Gemini 2.5 Flash-Lite.** Thinking is off by default; supported levels are low, medium and high ([thinking docs](https://aistudio.google.com/docs/thinking)) [V].
- **Gemma 4 26B.** OR shows `default_enabled: false` [V].

[I] Non-thinking mode is the right default for grounded answers and translation. It keeps the cost figures above valid and cuts latency. RuQualBench's top-6 Russian result for DeepSeek V4 Flash was measured in "Instant" (non-thinking) mode. Caveats:
- The Arena #32 result was measured in "Max" mode, so Russian fluency without thinking is a little less certain.
- Vectara does not say which mode it used.

If faithfulness or refusal behaviour is weak in tests, try `"effort": "low"` next.

## 5. Recommendation

The gate applied to every candidate, in order:
1. Vectara hallucination ≤ 5.0 % and answer rate ≥ 95 %.
2. *Positive* evidence of acceptable Russian.
3. No shutdown before 2027-05-14.
4. No training on prompts, or an easy opt-out.

Then take the cheapest route that passes.

| Candidate | Grounding | Russian | Deprecation | Data | Verdict |
|---|---|---|---|---|---|
| Gemma 4 26B ($0–0.30) | 5.2 %, borderline | ✓ | ✓ | ✓ | Cheapest overall, but over 5.0 %. Alternative only. |
| Gemma 3 12B ($0.52) | ✓ 4.4 % | no evidence | ✓ (old) | ✓ | Fails gate 2. |
| Mistral Small 2501 ($0.46) | 5.1 % | no evidence | single provider | ✓ | Fails. |
| **DeepSeek V4.1 Flash via OR ZDR ($0.44–1.02)** | ✓ 4.2 % | ✓ Arena-RU #32 | ✓ | ✓ (ZDR) | **Cheapest that passes every gate.** |
| Gemini 2.5 Flash-Lite ($1.12; $0 free tier, $0.56 flex) | ✓ 3.3 % (best non-deprecated) | weak | ✓ | ✓ | Fallback. |
| GPT-5.4 nano ($2.60) | ✓ 3.1 % | weak | ✗ (2027-04-01) | — | Fails. |

### Default: DeepSeek V4.1 Flash (1017 snapshot) via OpenRouter, ZDR-only, non-thinking
- **OpenRouter model ID:** `deepseek/deepseek-v4.1-flash-1017`. This is the same snapshot DeepSeek serves as `deepseek-flash` [V, OR description].
- **Direct DeepSeek ID** (not recommended for privacy reasons): `deepseek-flash`.
- **Request body additions:**
  ```json
  "reasoning": {"effort": "none"},
  "provider": {"zdr": true, "data_collection": "deny", "sort": "price"}
  ```
  The parameter names are verified in the [OR provider-selection docs](https://openrouter.ai/docs/guides/routing/provider-selection).
- **Expected cost:** about $0.67–1.02 per 1,000 queries at 8k+800, and $1.1–1.8 at 16k. Particle AI's flex endpoint ($0.44) is only eligible with the `:floor` suffix or flex routing, and it may queue.
- **Quantisation risk [I].** The cheapest ZDR endpoints are fp4/mxfp4 (Sail Research, Wafer). Aggressive quantisation may raise hallucination compared with whatever Vectara tested. To be safe, add `"quantizations": ["fp8"]`; the cheapest fp8 ZDR endpoint is DeepInfra at about $1.02 per 1,000 queries. Even that is below Gemini 2.5 Flash-Lite's standard price.

### Fallback: Gemini 2.5 Flash-Lite, thinking off (its default)
- **Google ID:** `gemini-2.5-flash-lite` (AI Studio / Gemini API).
- **OpenRouter ID:** `google/gemini-2.5-flash-lite`.
- **Why:** it has the lowest Vectara rate among non-deprecated models (3.3 %), comes from an independent vendor and infrastructure, and has clear EEA no-training terms. Its free tier covers the EEA too, so light use can cost $0. Paid use is $1.12 per 1,000 queries, or $0.56 on Flex.
- **On OpenRouter,** send it *without* `zdr: true`: its AI Studio endpoints are not on the ZDR list, so a request with that flag would find no route [V]. Implement the fallback as a separate request with its own provider settings, not as an entry in the same `models` array.
- **Before relying on it,** spot-check its Russian, since that evidence is weak.

### Cheaper alternative if the user accepts 5.2 %
Gemma 4 26B A4B:
- AI Studio free tier (`gemma-4-26b-a4b-it`, EEA terms) or OR `google/gemma-4-26b-a4b-it` on PrimeIntellect ZDR, at about $0.26–0.30 per 1,000 queries.
- Its Russian evidence is better than Gemini 2.5 Flash-Lite's.
- The OR `:free` variant is limited to a 32k max completion, and its providers' data terms are unknown. Avoid it for copyrighted texts [I].

[I] At about 1,000 queries per month, the default costs $1 or less per month. The spread between all compliant options is under $1.50 per month. A 30–50-question test on the user's own corpus would decide more than these leaderboards: check faithfulness, `[n]` correctness, refusal when the answer is absent, and Russian quality.

## 6. Corrections to the earlier notes

- **Gemini 2.5 Flash-Lite is not being redirected.** Google's deprecations page routes `gemini-2.5-flash` and `gemini-2.5-pro` from 2026-12-01. It says `gemini-2.5-flash-lite` "is not deprecated and remains available through the API until further notice" [V].
- **GPT-5.4 nano is deprecated,** with shutdown on 2027-04-01 (notice 2026-10-01) [V]. The earlier notes did not mention this.
- **DeepSeek V4.1 Flash costs far less on OpenRouter than on DeepSeek's own API.** Third-party OR endpoints charge $0.03–0.10 input and $0.11–0.70 output, against DeepSeek's $0.15/$0.60 off-peak and $0.30/$1.20 peak. Several of those endpoints are ZDR [V].
- **The cheapest V4.1 Flash listing ($0.57) is a temporary promotion** on Baidu (83.1 % discount), and it is not ZDR [V].

## 7. Open uncertainties / gaps

- **DeepSeek V4.1 Flash versions.** I could not confirm which snapshot Vectara tested (2026-09-10 or 1017), nor its reasoning mode. Arena-RU measured the 2026-09-10 snapshot in Max mode.
- **Russian Arena beyond rank 153.** The page shows only ranks 1–153. The HF datasets-server (`lmarena-ai/leaderboard-dataset`, updated 2026-11-13) returned errors on every query. I did not download the parquet file, per the no-download constraint. The exact Russian ratings of Gemini 2.5 Flash-Lite, Gemma 3 12B, Llama 3.3 70B and GPT-5.4 nano are therefore unknown, beyond being ≤ 1402 or unrated.
- **FACTS Grounding.** I could not read current values (the Kaggle page is JS-rendered).
- **Per-provider training flags on OR.** These are not in the public JSON. I relied on the ZDR list plus `data_collection: "deny"`. OR's own [privacy policy](https://openrouter.ai/privacy) (updated 2026-08-31) says it "does not use your Inputs or Outputs for model training", but it does not state a prompt-retention period.
- **Not verified this session:**
  - the Gemini OpenAI-compatibility layer;
  - Gemma 4's free-tier rate limits on AI Studio (the [rate-limits page](https://aistudio.google.com/docs/rate-limits) defers to the AI Studio UI);
  - OR's credit-purchase fee;
  - whether the Particle AI and Wafer endpoints are reliable enough for interactive use.
- **No Vectara score for GPT-6 Luna, Claude Haiku 5.5 or the Gemini 3.5+ Flash/Flash-Lite models.** If Vectara adds them, the choice may change. Re-check the [leaderboard](https://github.com/vectara/hallucination-leaderboard).
