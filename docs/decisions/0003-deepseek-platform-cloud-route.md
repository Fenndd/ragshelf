# 0003 — Cloud generation through the DeepSeek platform

- Status: accepted (2026-11-16). The user decided the route: use the DeepSeek platform with the user's own API key, and keep OpenRouter in the code as an unused alternative. The model ID, the thinking setting, and the configuration shape below were chosen by the assistant from the DeepSeek API documentation and are confirmed when T004 is accepted.
- Amends: [ADR 0001](0001-model-stack.md), row "Generation, cloud (default)"; everything else in ADR 0001 stands. Adds a second key to [ADR 0002](0002-pipeline-architecture.md) "Configuration", which names only `OPENROUTER_API_KEY`.
- Sources: DeepSeek API documentation read on 2026-11-16: [first API call](https://api-docs.deepseek.com/), [thinking mode](https://api-docs.deepseek.com/guides/thinking_mode), [models and pricing](https://api-docs.deepseek.com/quick_start/pricing).

## Context

ADR 0001 chose `deepseek/deepseek-v4.1-flash-1017` on OpenRouter with zero-data-retention routing as the default cloud model. No request was ever sent through that route: no OpenRouter key was configured. During T004 the user stated that OpenRouter will not be used for now and that an API key for the DeepSeek platform is available.

## Decision

| Item | Choice |
| --- | --- |
| Default cloud provider | DeepSeek platform, OpenAI-compatible API at `https://api.deepseek.com` (`POST /chat/completions`, `Authorization: Bearer <key>`). |
| Model | `deepseek-flash`. The documentation states this name is "now served by DeepSeek-V4.1-Flash-1017", the same model ADR 0001 selected. |
| Thinking | Disabled per request with `"thinking": {"type": "disabled"}`. The platform enables thinking by default; ADR 0001's reason for turning it off (billed as output, not needed for RAG answers) is unchanged. |
| Key | `DEEPSEEK_API_KEY` in `.env`. The prototype used this name for an OpenRouter key, so the client refuses a value that starts with `sk-or-` instead of sending it to DeepSeek. |
| OpenRouter | Kept as a selectable provider with the ADR 0001 settings (`reasoning.effort = "none"`, `provider = {zdr: true, data_collection: "deny", sort: "price"}`), key in `OPENROUTER_API_KEY`. Not the default and not exercised. |
| Configuration | `llm.route` stays `cloud` or `local`. `llm.cloud_provider` selects `deepseek` (default) or `openrouter`; each provider has its own section (`llm.deepseek`, `llm.openrouter`) with defaults in `src/ragshelf/config.py`, overridable in `ragshelf.toml`. |

The local route and query translation (ADR 0001) are unchanged: in cloud mode both use the default cloud provider.

## Consequences

- Data handling changes. ADR 0001 chose OpenRouter partly for zero-data-retention endpoints that do not train on prompts. Those routing settings do not exist on the DeepSeek platform route: queries and the retrieved document text are sent to DeepSeek under its own terms and privacy policy, which were not reviewed for this decision. Anyone who needs the zero-retention guarantee switches `llm.cloud_provider` to `openrouter` and supplies that key.
- `deepseek-flash` is an alias that the platform can repoint. The model named in each response is recorded with the answer (T014 traces) so a change is visible.
- Cost, computed from the pricing page of 2026-11-16 for 8k input tokens (cache miss) and 800 output tokens: about $1.68 per 1,000 queries off-peak and $3.36 at peak hours (01:00–04:00 and 06:00–10:00 UTC on weekdays), against ADR 0001's estimate of $0.70 on the cheapest OpenRouter endpoint. Cached input is billed far lower ($0.003–$0.006 per 1M tokens).
- The quality evidence in ADR 0001 (hallucination rate, Russian ranking) was collected for the same model and carries over; it is still to be confirmed on the project's own documents (T015, T018).
- The OpenRouter client keeps its unit tests but has never been run against the real endpoint.
- The official platform documentation for the base URL, model identifier, and disabled-thinking request field was freshly verified on 2026-11-16. A real call through `create_chat_client(load_settings(), load_secrets(), route='cloud').complete(...)` then succeeded with model `deepseek-flash`, route `cloud`, 22 prompt + 76 completion = 98 total tokens, and `finish_reason: stop`. It returned a non-empty, correct two-sentence Russian explanation of RAG; the request details are recorded in T004's Result.
