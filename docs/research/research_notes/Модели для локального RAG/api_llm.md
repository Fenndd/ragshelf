# Cloud API LLMs for RAG answer generation (as of 2026-11-14)

Scope: hosted LLM APIs for grounded answer generation from retrieved chunks in a personal, single-user RAG system. Typical query: about 8k input and 800 output tokens, with 4k–16k of retrieved context. Answers are mostly in Russian, from mostly English sources. The current integration is `deepseek/deepseek-chat-v3-0324:free` through OpenRouter's OpenAI-compatible API.

Method and caveats: I used web searches and fetched pages on 2026-11-14. I signed up for nothing and called no APIs. Wherever I could, the prices come from official pricing pages fetched that day: DeepSeek, Google AI Studio, OpenAI and Anthropic. Third-party aggregators often disagree with each other, and every figure taken from one is marked as such. Many model names here (GPT-6 Luna, Haiku 5.5, Gemini 3.8 Flash, DeepSeek V4.1 Flash and so on) are newer than my built-in knowledge. Their names and prices are exactly what the fetched pages showed.

Per-query cost formula used below: `cost = 8,000 × input_price/1M + 800 × output_price/1M`. The monthly figure is that cost × 1,000. Neither includes caching, the OpenRouter credit-purchase fee, or reasoning ("thinking") tokens. Thinking tokens are billed as output and can multiply the output cost.

## 1. Status of OpenRouter free models and other free tiers; is the DeepSeek free route still available?

### Takeaway
The project's current model ID, `deepseek/deepseek-chat-v3-0324:free`, appears to be retired: both OpenRouter model-page URLs returned HTTP 404 on 2026-11-14. OpenRouter `:free` models in general still exist, limited to 20 RPM and 50 requests/day, or 1,000/day after at least $10 of all-time credit purchases. For a user in the EU, the most realistically usable free option is the Google Gemini API free tier. Inside the EEA, Google applies its paid-tier data terms (no training on prompts) to the unpaid quota as well.

### Cited Findings
- **The DeepSeek free route is probably gone.** `https://openrouter.ai/deepseek/deepseek-chat-v3-0324:free` and `https://openrouter.ai/models/deepseek/deepseek-chat-v3-0324:free` both returned HTTP 404 when fetched on 2026-11-14 — [OpenRouter model page](https://openrouter.ai/deepseek/deepseek-chat-v3-0324:free), [alt URL](https://openrouter.ai/models/deepseek/deepseek-chat-v3-0324:free). Search-engine snippets still show the page as "Free, 131K context, created Mar 24, 2025", but those are cached and undated. The 404 is newer evidence.
- A third-party article surfaced in search reported that DeepSeek R1, DeepSeek V4 Flash, Qwen3 Coder and Kimi K2.6 lost `:free` status around June 2026. I did not open the article itself, and the exact source is ambiguous between [klymentiev.com (June 2026)](https://klymentiev.com/blog/openrouter-free-tier) and [aireiter.com](https://aireiter.com/blog/best-free-openrouter-models-for-programming-2026). Treat this as low confidence.
- OpenRouter's own docs say free-model availability changes often, offer an `openrouter/free` router that picks among currently available free models, and point to the models page as the source of truth — [OpenRouter Free Models Router docs](https://openrouter.ai/docs/guides/routing/routers/free-router).
- **Official OpenRouter free limits (fetched 2026-11-14):**
  - 20 requests/minute.
  - 50 requests/day if all-time credit purchases are under 10 credits; 1,000/day with at least 10.
  - The daily counter resets on the UTC day.
  - A negative balance can cause errors even on free models.
  - BYOK requests are not gated by these limits.

  Source: [OpenRouter Limits docs](https://openrouter.ai/docs/api-reference/limits).
- OpenRouter's docs reportedly say that extra accounts or API keys do not raise limits ("we govern capacity globally"), and free models are reported to be throttled heavily at peak hours. Both claims come from secondary write-ups dated around October 2026 — [fast.io](https://fast.io/resources/openrouter-rate-limit.md), [truefoundry](https://www.truefoundry.com/de/blog/openrouter-rate-limits-your-free-tier-depends-on-what-youve-already-paid).
- OpenRouter's own comparison of free APIs is dated 2026-06-15, updated 2026-09-24, and built on April 2026 provider docs. It lists:
  - **OpenRouter:** 20 RPM, 50/1,000 RPD, no training.
  - **Google AI Studio:** 5–15 RPM, 20–1,500 RPD, data used for training "outside EU/UK/EEA".
  - **Groq:** 30 RPM, 1,000 RPD, no training.
  - **Cerebras:** 30 RPM, about 1M tokens/day, no training.
  - **Mistral:** about 1B tokens/month, training "Yes (Experiment tier)".
  - **Others:** Cloudflare Workers AI (2K–8K context), GitHub Models (15 RPM, 150–1,000/day), Cohere (non-commercial, about 100/day) and NVIDIA NIM (about 1,000/day).

  Source: [OpenRouter blog: Free LLM APIs Compared](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/). Note that the article is itself a vendor's blog.
- **Gemini free tier:** the official pricing page (fetched 2026-11-14) shows a free tier for Gemini 3.8 Flash, 3 Flash Preview, 3.5 Flash-Lite, 3.1 Flash-Lite and 2.5 Flash-Lite, but not for Gemini 3.1 Pro Preview — [Gemini API pricing](https://aistudio.google.com/docs/pricing). The page I fetched did not include per-model free-tier RPM/RPD numbers.
- **Mistral Experiment (free) plan:** Mistral's help center says API requests on the Experiment plan may be used to train Mistral models — [Mistral help center](https://help.mistral.ai/en/articles/450104-how-can-i-try-the-api-for-free-with-the-experiment-plan). Third-party guides say it needs a verified phone number but no card. They disagree on the limits: either 1 req/s and 500K TPM, or about 2 RPM and 1B tokens/month — [activepieces](https://www.activepieces.com/blog/mistral-api-free-tier-limits-models-credits-2026.md), [costbench](https://costbench.com/software/llm-api-providers/mistral-ai/free-plan/).
- **Cerebras:** official docs say every model in the public catalog is available on the Free Trial tier with per-model limits, and buying credits moves an account to a Developer tier without hourly or daily token caps — [Cerebras rate limits](https://inference-docs.cerebras.ai/support/rate-limits). Third-party figures for the trial are about 5 RPM, 30K–90K TPM and 1M tokens/day, with models such as gpt-oss-120b, zai-glm-4.7 and gemma-4-31b — [freeapihub](https://freeapihub.com/blog/cerebras-vs-groq-fast-inference-api), [claudelog](https://claudelog.com/faqs/is-cerebras-free/).
- **Groq:** third-party figures are about 30 RPM, 1,000 RPD, 6K–8K TPM and 200K tokens/day for some models, such as qwen/qwen3.6-27b — [aireiter](https://aireiter.com/blog/free-llm-api-quota-comparison), [freeapihub](https://freeapihub.com/blog/cerebras-vs-groq-fast-inference-api). These conflict with a claim that Groq publishes no fixed per-model limits — [apidog](https://apidog.com/blog/together-fireworks-groq-free-tiers/).
- **DeepSeek direct:** one write-up mentions a trial of about 10M tokens — [OpenRouter blog](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/). Unverified on DeepSeek's site.

### Inferences
- The current config is likely broken, or will break, and should be migrated. A query at 8k input tokens is small, so the binding free-tier constraint is requests/day, not tokens.
- At 50 RPD, OpenRouter `:free` covers light personal use (about 1,500 queries/month at most). A one-time $10 credit purchase raises that to 1,000 RPD. Free models still rotate, and their providers may log or train on prompts (see Q5).
- Groq's 6K–8K TPM limit, as reported, would block single requests with 8k–16k of context. Cerebras's TPM limit (30K–90K) fits 1–3 queries/minute.
- Mistral's free tier trains on prompts, which is a poor fit for copyrighted source texts.
- Best free option for an EU user: the Gemini API free tier (Flash-Lite or Flash), because EEA data terms apply (Q5). Second choice: OpenRouter `:free` with the `openrouter/free` router or 2–3 fallback IDs.

### Gaps
- The live list of OpenRouter `:free` models on 2026-11-14. The models page is JS-rendered, and I deliberately did not query the models API.
- Official per-model free-tier RPM/RPD for Gemini 3.x in November 2026. The rate-limits page was not fetched.
- Official Groq free-tier limits for November 2026.

## 2. Best paid quality-per-price models; prices, cost per query and per 1,000 queries

### Takeaway
In November 2026 the cheapest capable options cost about $1–3.50 per 1,000 RAG queries. Prices at that level: GPT-6 Luna and Claude Haiku 5.5 are both $0.10/$0.50, Gemini 2.5 Flash-Lite is $0.10/$0.40, and DeepSeek V4.1 Flash is $0.30/$1.20 at peak and half that off-peak. For Russian-language quality, Gemini 3.8 Flash ranks near the top of the Russian Arena (#4) at $0.75/$3.75 (about $9/1,000 queries) until 2026-12-31, after which its price doubles.

### Cited Findings
Prices are USD per 1M input/output tokens, standard (non-batch) rates, from official pages fetched on 2026-11-14 unless marked otherwise.

| Model | Input | Output | Cached input | Cost / query (8k+800) | Cost / 1,000 queries | Source |
|---|---|---|---|---|---|---|
| DeepSeek V4.1 Flash (`deepseek-flash`), peak | $0.30 | $1.20 | $0.006 | $0.00336 | $3.36 | [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing) |
| DeepSeek V4.1 Flash, off-peak | $0.15 | $0.60 | $0.003 | $0.00168 | $1.68 | same |
| DeepSeek V4 Pro (`deepseek-v4-pro`), peak | $1.32 | $3.96 | $0.044 | $0.01373 | $13.73 | same |
| DeepSeek V4 Pro, off-peak | $0.66 | $1.98 | $0.022 | $0.00686 | $6.86 | same |
| Gemini 3.8 Flash (introductory price until 2026-12-31) | $0.75 | $3.75 | $0.075 | $0.0090 | $9.00 | [Gemini pricing](https://aistudio.google.com/docs/pricing) |
| Gemini 3.8 Flash (from 2027-01-01) | $1.50 | $7.50 | $0.15 | $0.0180 | $18.00 | same |
| Gemini 3 Flash Preview | $0.50 | $3.00 | $0.05 | $0.0064 | $6.40 | same |
| Gemini 3.5 Flash-Lite | $0.30 | $2.50 | $0.03 | $0.0044 | $4.40 | same |
| Gemini 3.1 Flash-Lite | $0.25 | $1.50 | $0.025 | $0.0032 | $3.20 | same |
| Gemini 2.5 Flash-Lite | $0.10 | $0.40 | $0.01 | $0.00112 | $1.12 | same |
| Gemini 3.1 Pro Preview (≤200k) | $2.00 | $12.00 | $0.20 | $0.0256 | $25.60 | same |
| GPT-6 Luna (`gpt-6-luna`) | $0.10 | $0.50 | $0.01 | $0.0012 | $1.20 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |
| GPT-5.6 Luna | $0.20 | $1.20 | $0.02 | $0.00256 | $2.56 | same |
| GPT-5.4 nano | $0.20 | $1.25 | $0.02 | $0.0026 | $2.60 | same |
| GPT-5.4 mini | $0.75 | $4.50 | $0.075 | $0.0096 | $9.60 | same |
| GPT-5 nano (older) | $0.05 | $0.40 | $0.005 | $0.00072 | $0.72 | same |
| GPT-5 mini (older) | $0.25 | $2.00 | $0.025 | $0.0036 | $3.60 | same |
| GPT-6.1 Terra | $1.00 | $5.00 | $0.05 | $0.0120 | $12.00 | same |
| Claude Haiku 5.5 (prompts ≤100K) | $0.10 | $0.50 | $0.01 (hit) | $0.0012 | $1.20 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Haiku 4.5 | $1.00 | $5.00 | $0.10 | $0.0120 | $12.00 | same |
| Claude Sonnet 5 / 5.5 | $2.00 | $10.00 | $0.20 / $0.10 | $0.0240 | $24.00 | same |
| Qwen3.5-Plus (third-party figure) | $0.40 | $2.40 | n/a | $0.00512 | $5.12 | [usagepricing](https://www.usagepricing.com/ai-token-pricing/compare/kimi-k2-6-vs-qwen3-5-plus) (unverified) |
| Kimi K2.6 (third-party, Aug–Sep 2026) | ~$0.96 | ~$3.97 | n/a | ~$0.0109 | ~$10.86 | [anotherwrapper](https://anotherwrapper.com/llm-pricing/kimi-k2.6) (unverified) |
| GLM-5 (third-party) | ~$1.00 | ~$3.20 | n/a | ~$0.0106 | ~$10.56 | [anotherwrapper](https://anotherwrapper.com/tools/llm-pricing/glm-5/kimi-k2.6) (unverified) |
| Mistral Small 4 / 2603 (third-party; sources conflict) | $0.10–0.20 | $0.30–0.60 | n/a | $0.0010–0.0021 | $1.04–2.08 | [pricepertoken](https://pricepertoken.com/pricing-page/model/mistral-ai-mistral-small-2603), [curlscape](https://curlscape.com/blog/mistral-api-pricing-2026) (unverified) |

- **DeepSeek details** — [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing):
  - Off-peak is half the peak price. Peak hours are 01:00–04:00 and 06:00–10:00 UTC, Monday to Friday (02:00–05:00 and 07:00–11:00 CET in winter). Weekends and Chinese public holidays are off-peak.
  - Both models default to thinking mode.
  - `deepseek-v4-flash` is retired and its requests are served by V4.1-Flash-1017.
  - The page does not mention `deepseek-chat` or `deepseek-reasoner`.
  - V4 Pro prices were reportedly raised on 2026-08-16 — [BenchLM](https://www.benchlm.ai/deepseek/api-pricing). Older mid-2026 listings ($0.14/$0.28 for Flash, $0.435/$0.87 for Pro) are stale.
- **Gemini deprecations** — [Gemini pricing](https://aistudio.google.com/docs/pricing):
  - From 2026-12-01, `gemini-2.5-flash` routes to Gemini 3.5 Flash-Lite, and `gemini-2.5-pro` routes to Gemini 3.8 Flash, each billed at the new model's rates.
  - 2.5 Flash-Lite is still listed. A third-party guide claimed it retires on 2026-10-16, which contradicts the official listing — [search summary of Gemini guides](https://www.cloudzero.com/blog/gemini-pricing/).
- **Claude Haiku 5.5:**
  - Prompts over 100K tokens are billed at $0.50/$2.50.
  - Batch is $0.05/$0.25.
  - US-only inference (`inference_geo`) costs 1.1×.
  - Haiku 5.5 is excluded from the 1M-context-at-standard-price rule.

  Source: [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- **OpenAI:**
  - These are short-context rates (≤272K input). Long-context rates are higher.
  - Batch is about half price.
  - Regional processing (data-residency) endpoints add a 10% uplift for models released on or after 2026-03-05.

  Source: [OpenAI pricing](https://developers.openai.com/api/docs/pricing).
- **16k-context variant:** double the input part of each estimate. For example, DeepSeek Flash at peak becomes $0.0048 + $0.00096 = $0.00576/query ($5.76/1,000), and GPT-6 Luna or Haiku 5.5 become $0.0016 + $0.0004 = $0.002/query ($2.00/1,000). This is arithmetic from the table above.

### Inferences
- At 1,000 queries/month every candidate below Sonnet costs under about $15/month, and most cost $1–5. Quality and data terms should drive the choice, not price.
- RAG prompts differ every query, so prompt caching only saves on the fixed system prompt or instructions (about 0.5–1k tokens). The savings are marginal for this profile.
- Thinking mode (the DeepSeek default; also the "High/Max" variants on Arena) can multiply the output-token cost. For grounded answer generation, non-thinking mode is likely enough and keeps the costs above valid.

**Ranked recommendation (my synthesis; check against Q3–Q5):**

1. **Best quality for Russian answers: Gemini 3.8 Flash** (paid tier).
   - Ranks #4 on the Russian Arena, the top non-Pro model.
   - About $9/1,000 queries until 2026-12-31, then about $18.
   - EU-friendly data terms.
   - No Vectara grounding score found (gap).
2. **Best value: DeepSeek V4.1 Flash direct** (about $1.7–3.4/1,000 queries).
   - Vectara hallucination 4.2% (top 6), Russian Arena #32 in "Max" mode.
   - Weak on data terms: servers in China, training by default (Q5). For copyrighted books, consider routing the same model through an OpenRouter provider that doesn't train, if one exists (not verified).
   - Value alternatives with stronger data terms: **Claude Haiku 5.5** or **GPT-6 Luna** (about $1.2/1,000). Neither has a verified hallucination or Russian Arena score at the top tier (Luna is Arena #102). **Gemini 3.1/3.5 Flash-Lite** ($3.2–4.4) also fits.
3. **Free: Gemini API free tier** (Flash / Flash-Lite) for an EEA user, since paid-tier data terms apply. Fallback: OpenRouter `:free` with the `openrouter/free` router. Replace the dead DeepSeek ID.

### Gaps
- Official Mistral, Qwen (Alibaba Model Studio international), Moonshot (Kimi) and Z.ai (GLM) pricing pages were not fetched. The figures in the table are third-party.
- OpenRouter's pass-through pricing and the credit-purchase fee for these models were not verified.
- Context window sizes for Gemini 3.x, GPT-6 Luna and Haiku 5.5 were not confirmed this session.

## 3. RAG-specific quality: faithfulness, hallucination, citation following, long context

### Takeaway
On Vectara's summarization-faithfulness leaderboard (updated 2026-10-22), several budget models lead: GPT-5.4 nano (3.1%), Gemini 2.5 Flash-Lite (3.3%) and DeepSeek V4.1 Flash (4.2%). Several newer and larger models do worse, including DeepSeek V4 Pro (8.6%), Claude Haiku 4.5 (9.8%) and Gemini 3 Flash Preview (13.5%). I found no 2026 FACTS Grounding or long-context numbers for the newest cheap models (GPT-6 Luna, Haiku 5.5, Gemini 3.8 Flash).

### Cited Findings
- **Vectara HHEM hallucination leaderboard, last updated 2026-10-22** — [GitHub vectara/hallucination-leaderboard](https://github.com/vectara/hallucination-leaderboard). Hallucination rate, with answer rate in parentheses:
  - **Top overall:** antgroup finix_s1_32b 1.8%; GPT-5.4-nano 3.1% (100%); Gemini 2.5 Flash-Lite 3.3% (99.5%); Phi-4 3.7%; Llama-3.3-70B 4.1%; DeepSeek V4.1 Flash 4.2% (99.9%); Mistral Large 2411 4.5%; Qwen3-8B 4.8%.
  - **DeepSeek:** V3 6.1%; V3.1 5.5%; V3.2 6.3%; V3.2-Exp 5.3%; V4.1 Flash 4.2%; V4 Pro 8.6%; R1 11.3%.
  - **Gemini:** 2.5 Flash-Lite 3.3%; 2.5 Flash 7.8%; 3.1 Flash-Lite Preview 8.2%; 3 Flash Preview 13.5%.
  - **OpenAI:** GPT-5.4 nano 3.1%; GPT-5.4 mini 5.5%; GPT-5 nano 10.5%; GPT-5 mini 12.9%.
  - **Anthropic:** Claude Haiku 4.5 9.8%.
  - **Qwen:** Qwen3.5-Flash 10.5%; Qwen3.5-Plus 10.7%.
  - **Kimi:** K2.6 10.8%.
  - **GLM:** GLM-5 10.1%.
  - **Mistral:** Mistral 3 Large 14.5%; Mistral Medium 2508 22.7%.
- Vectara measures faithfulness when summarizing supplied documents with the HHEM-2.3 judge model. That is close to RAG grounding, but it does not test citation following or recall without a source — [dev.co summary](https://dev.co/ai/frameworks/hallucination-leaderboard). A newer, harder Vectara dataset exists, and its rates are not comparable to the original — [suprmind](https://suprmind.ai/hub/ai-hallucination-rates-and-benchmarks/).
- **FACTS Grounding:** GPT-5.2 reportedly led the Kaggle FACTS Grounding benchmark at 76.17% (secondary source dated 2026-03-25) — [AI Benchmark Digest](https://buttondown.com/doroshenko/archive/ai-benchmark-digest-2026-03-25/). The FACTS Benchmark Suite announced in December 2025 (older) gave Gemini 3 Pro an overall FACTS Score of 68.8%, a composite of grounding, multimodal, parametric and search — [Google DeepMind blog](https://deepmind.google/blog/facts-benchmark-suite-systematically-evaluating-the-factuality-of-large-language-models/). Grounding v2 changed the judge models, so v1 and v2 scores are not comparable — [same](https://deepmind.google/blog/facts-benchmark-suite-systematically-evaluating-the-factuality-of-large-language-models/).
- **Long context:**
  - BenchLM MRCRv2 (8-needle), update of 2026-11-06: Sakana Fugu-Ultra 93.6%, Qwen3.8 Max 92.9%, Qwen3.7 Plus 91.7%. The top scores are close to saturation — [BenchLM MRCRv2](https://www.benchlm.ai/benchmarks/mrcrV2).
  - A June 2026 BenchLM snapshot had Gemini 3.5 Flash at 77.3% — [same](https://benchlm.ai/benchmarks/mrcrv2).
  - MRCR 1M (May–July 2026): Claude Opus 4.6 92.9%, DeepSeek V4 Pro 83.5% — [benchmarklist MRCR 1M](https://benchmarklist.com/benchmarks/mrcr_1m/).
  - Fiction.LiveBench snapshots have no Gemini 3 or DeepSeek V4 rows — [DataLearner](https://www.datalearner.com/en/benchmarks/fiction-livebench).

### Inferences
- For the 4k–16k-token context in this project, long-context ability (≥128k) barely matters, because every candidate handles 16k. Faithfulness to the provided context matters more, and that favors DeepSeek V4.1 Flash, GPT-5.4 nano and Gemini 2.5 Flash-Lite on Vectara.
- On Vectara, newer or larger models are not reliably better. Gemini 3 Flash Preview and DeepSeek V4 Pro score worse than their smaller siblings. A small project-level evaluation on the user's own documents and questions would be more decisive than any leaderboard.

### Gaps
- Vectara rows for GPT-6 Luna, GPT-5.6 Luna, Claude Haiku 5.5, Gemini 3.5/3.8 Flash and 3.5 Flash-Lite were not in the fetched data. They may not have been added yet.
- No current (November 2026) FACTS Grounding leaderboard values for the candidates. The Kaggle page was not fetched.
- No benchmark specifically on citation following, such as producing `[n]` markers that point to the correct chunk, was found for these models.
- RULER results for 2026 models were not found.

## 4. Quality of answers in Russian (and Slovak) from English sources

### Takeaway
The Russian Text Arena (snapshot of 2026-11-11, about 983k votes, 385 models) puts Gemini Flash models at the top of the price-efficient set: 3.8 Flash and 3.7 Flash rank #4–5, ahead of most Claude Opus models. DeepSeek V4.1 Flash (Max) is #32, Qwen3.8-Max #26 and Kimi K3 #21. Ultra-cheap GPT-6 Luna (#102) and Gemini 3.1 Flash-Lite Preview (#103) are well behind. I found no Slovak-specific benchmark.

### Cited Findings
- **Russian Text Arena** (Nov 11, 2026; 983,417 votes; 385 models) — [arena.ai Russian leaderboard](https://arena.ai/leaderboard/text/russian):
  - **Top:** #1 Gemini 4 Carbon (High) 1547 (preliminary); #2 Gemini 4 Argon (High) 1532; #4 Gemini 3.8 Flash (High) 1516 (preliminary, 8,741 votes); #5 Gemini 3.7 Flash (High) 1516; Claude Fable 5 / Opus 5.5 1514; #14 GPT-5.6 Sol 1498.
  - **Gemini Flash family:** 3.6 Flash #23 (1492); 3.5 Flash #24–25 (1491–1492); 3 Flash #29 (1486); 3.5 Flash-Lite #60 (1463); 3.1 Flash-Lite Preview #103 (1434).
  - **DeepSeek:** V4.1-Flash-20260910 (Max) #32 (1481); V4-Pro #63 (1461); V4-Flash #104 (1432); V3.2 #118 (1422).
  - **OpenAI:** GPT-5.4 mini (High) #78 (1451); GPT-5.6 Luna (xHigh) #87 (1446); GPT-6 Luna (Max) #102 (1437).
  - **Anthropic:** Claude Haiku 4.5 is around row 154. Haiku 5.5 was not seen.
  - **Qwen:** 3.8-Max #26 (1491); 3.7-Plus #64 (1458).
  - **Kimi:** K3 (Max) #21 (1493); K2.6 #74 (1453).
  - **GLM:** 5.3 (Max) #36 (1480); 5.3-Flash #47 (1472).
  - **Mistral:** Large 4 #117 (1422).
- **MERA** (Russian benchmark by the AI Alliance): MERA Text 2.0 was released on 2026-09-01 with 12 private tests (Human-Centric, Culture-Specific, Agentic, Reasoning), and MERA Reason launched in July 2026 — [MERA news](https://mera.a-ai.ru/en/news/Reasoning,%20Agentic,%20Text). The leaderboard page fetched on 2026-11-14 rendered no data (JS) — [MERA Text leaderboard](https://mera.a-ai.ru/en/text/leaderboard).

### Inferences
- Arena measures general chat preference in Russian, not grounded translation-plus-synthesis from English chunks. It is still the best available proxy for Russian fluency.
- The ranking suggests that Gemini 3.8 Flash gives the best Russian output per dollar among mid-priced models. DeepSeek V4.1 Flash is decent and much cheaper.
- "High/Max" variants are reasoning modes. A non-thinking call to the same model may score lower in Russian.
- Slovak quality is unverified. Gemini and GPT/Claude-class models generally have broad EU-language coverage, but I found no evidence this session.

### Gaps
- No MERA scores were retrieved, because the page is JS-rendered.
- No Slovak-language leaderboard or benchmark was found. I did not search an Arena "Slovak" tab or Slavic-language evaluations. A targeted search is still needed.
- No benchmark specifically on cross-lingual grounded answering (English context → Russian answer) was found.

## 5. Data handling (logging, retention, training) and EU availability

### Takeaway
For copyrighted books and articles, the safest options are paid or EEA-covered tiers of Google, OpenAI and Anthropic. Google's terms explicitly apply its paid data-use rules, with no training on prompts, to free Gemini API quota for EEA, Swiss and UK users. Free tiers elsewhere (Mistral Experiment, OpenRouter free providers, Gemini outside the EEA) may train on prompts. DeepSeek's direct API stores data in China and reportedly trains by default, with an opt-out for EU users.

### Cited Findings
- **Gemini API Additional Terms** (effective 2026-03-23) — [Gemini API terms](https://aistudio.google.com/docs/terms):
  - **Unpaid Services:** content is used to improve Google products and ML. Human reviewers "may read, annotate, and process your API input and output". The terms warn against submitting confidential information.
  - **Paid Services:** prompts and responses are not used for product improvement. They are logged "for a limited period of time" for safety and policy enforcement, under a Data Processing Addendum.
  - **EEA, Switzerland and UK:** the paid data-use terms "apply to all Services, including Google AI Studio and unpaid quota in the Gemini API". Users there "may use only Paid Services when making API Clients available to users".
- The Gemini pricing page likewise marks free-tier content as "used to improve our products" and paid-tier content as not used — [Gemini pricing](https://aistudio.google.com/docs/pricing).
- **OpenRouter** — [OpenRouter privacy and logging docs](https://openrouter.ai/docs/features/privacy-and-logging):
  - Account settings let users opt out of providers that may train ("OpenRouter will not route to providers that train"), with separate settings for paid and free models.
  - Provider retention policies are listed per endpoint, and routing does not change based on them.
  - A ZDR ("no routine storage after processing") tier and a "Safety Retention" tier exist.
  - EU regional endpoints, which keep prompts and completions in the region, are available only on Business and Enterprise plans.
- **Mistral Experiment (free):** requests may be used for training — [Mistral help center](https://help.mistral.ai/en/articles/450104-how-can-i-try-the-api-for-free-with-the-experiment-plan). An opt-out reportedly exists in the Admin Privacy settings, which I did not verify — [search summary](https://grizzlypeaksoftware.com/articles/p/mistral-ai-pricing-in-2026-pro-costs-free-tier-limits-and-api-rates-lx4o2n2v).
- **DeepSeek:**
  - Its privacy policy says data is stored on "secure servers located in the People's Republic of China" — [DeepSeek privacy policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html), via search summary; the full text was not fetched.
  - Secondary sources say training is a default purpose with an opt-out for European users, there is no ZDR, and retention is undefined — [developersdigest](https://www.developersdigest.tech/models/data-retention/deepseek), [sonomos](https://sonomos.ai/blog/is-deepseek-safe-gdpr-hipaa-2026/).
  - A February 2026 policy update added GDPR legal bases and an EU representative. Earlier there was regulatory action in Italy and Germany — [macaron](https://macaron.im/de/blog/deepseek-v4-gdpr-eu). Sources conflict on whether the API terms cover training.
- **Anthropic:** US-only inference via `inference_geo` costs 1.1× — [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing). The default is global routing.
- **OpenAI:** regional processing (data residency) endpoints carry a 10% uplift — [OpenAI pricing](https://developers.openai.com/api/docs/pricing).

### Inferences
- **Copyrighted content:** Sending book or article excerpts to a provider that trains on inputs could arguably redistribute that content into training data. Paid tiers or EEA-covered tiers are the cleaner choice. For an EU-based user, the Gemini free tier is unusually good on this point.
- **OpenRouter:** If the project keeps using OpenRouter, turn on the "no training" setting for both free and paid models and prefer ZDR endpoints. Note that the opt-out may remove most `:free` endpoints. This is my inference from how the routing works and was not verified.
- **DeepSeek direct:** The cheapest strong option, but the weakest on data terms for EU users.

### Gaps
- Official API data-retention and training terms for OpenAI, Anthropic, Groq, Cerebras, Moonshot, Z.ai and Alibaba were not fetched this session.
- Explicit regional availability (whether service is offered in the EU) was verified only for Gemini, through the terms' EEA clauses. For the others, I found no restriction but did not check supported-country lists.
- Which OpenRouter providers serve DeepSeek V4.1 Flash with no-training or ZDR terms is unverified.

## 6. Integration: OpenAI-compatible endpoints, structured output, context windows, prompt caching

### Takeaway
OpenRouter, the current integration, stays the lowest-friction path, because one OpenAI-compatible client reaches every model above. All the major direct providers offer cached-input discounts, roughly 90–98% off input. That matters little here, because retrieved context differs on every query. DeepSeek V4.x offers 1M context; OpenAI's base rates apply up to 272K input.

### Cited Findings
- **DeepSeek:**
  - `deepseek-flash` and `deepseek-v4-pro` have a 1M context. The page lists a maximum output of 384K without saying which model it applies to.
  - Concurrency limits are 2,500 (Flash) and 500 (Pro).
  - Thinking and non-thinking modes are available, with thinking as the default.
  - A cache hit costs $0.006 versus $0.30 for a miss at peak, about 98% off.

  Source: [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing).
- **Gemini:** context caching costs about 10% of the input price plus a storage fee (for example $0.075 vs $0.75 for 3.8 Flash; $0.01 vs $0.10 for 2.5 Flash-Lite) — [Gemini pricing](https://aistudio.google.com/docs/pricing).
- **OpenAI:** cached input is 10% of the input price (for example $0.01 vs $0.10 for GPT-6 Luna). Standard rates apply up to 272K input tokens, with higher long-context rates above that — [OpenAI pricing](https://developers.openai.com/api/docs/pricing).
- **Anthropic** — [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing):
  - Cache writes cost 1.25× base (5 min) or 2× base (1 h). Cache hits cost 0.1× base for Haiku 5.5, and 0.05× for Sonnet 5.5 and Opus 5.5.
  - Claude 4.6+ models get 1M context at standard price, except Haiku 5.5, which has tiered pricing above 100K.
  - The minimum cacheable prompt for Haiku 5.5 is 286 tokens.
- **OpenRouter:** the project's existing integration is OpenAI-compatible chat completions, and OpenRouter supports fallback lists and the `openrouter/free` router — [OpenRouter free router docs](https://openrouter.ai/docs/guides/routing/routers/free-router).

### Inferences
- **Lowest-effort migration:** keep the OpenRouter client and change the model ID, for example to a DeepSeek V4.1 Flash route, a Gemini Flash route or `openrouter/free`.
- **Going direct:** DeepSeek's and Google's own APIs would need endpoint and key changes. Their OpenAI-compatibility layers are not verified this session (see Gaps).
- **Caching:** only the static system prompt benefits. Expect under 10% savings for this RAG profile.
- **Structured output:** needed only if answers must carry machine-readable citations. In that case, prefer providers with JSON-schema structured output, after verifying support per model.

### Gaps
- I did not verify, for each provider this session, OpenAI-compatible endpoint support (DeepSeek, Gemini's OpenAI compatibility layer, Anthropic's OpenAI SDK compatibility, Mistral, Groq, Cerebras), JSON-schema structured output, or context window sizes for Gemini 3.x, GPT-6 Luna and Haiku 5.5. These should be checked in each provider's API docs before implementation.
- Whether OpenRouter passes provider caching discounts through for DeepSeek and Gemini routes was not verified.
