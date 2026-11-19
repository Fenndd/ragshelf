---
id: T011
title: Add query translation to English
milestone: M3
status: done
depends_on: [T004]
area:
  - "src/ragshelf/retrieve/__init__.py"
  - "src/ragshelf/retrieve/translate.py"
  - "src/ragshelf/prompts/**"
  - "tests/retrieve/test_translate.py"
---

# T011 — Add query translation to English

## Goal

Translate non-English queries to English before retrieval while keeping the original for the answer language and the trace.

## Sources

- [Query translation row in ADR 0001](../docs/decisions/0001-model-stack.md)
- [Retrieval in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: Language detection of the query (by the LLM response or a light detector chosen in the task and justified in Result), translation through the `ChatClient` with a versioned prompt that returns only the translation, English queries passed through unchanged, failure raises instead of silently using the original.

Out of scope: Multi-query rewriting or HyDE (candidate experiments after the baseline).

## Acceptance Criteria

1. Unit tests with the scripted client cover ru, sk, en pass-through, and failure.
2. On 10 ru and 10 sk gold-set queries through the cloud route, the translations are reviewed and recorded in Result.

## Checks

- `venv/Scripts/python.exe -m pytest tests/retrieve/test_translate.py`
- Manual review of 20 translations.

## Open Questions

None

## Result

### Acceptance — 2026-11-19

Accepted under the user's conditional instruction, "Можно их принимать тоже. Вроде бы всё согласовали, уточни" (accept these too after checking the agreed state), and explicitly confirmed by the user on 2026-11-19: "Просмотрел. Принимаю T006 и T011." The acceptance check confirmed both criteria: the recorded scripted-client suite passed 119 tests, and the required cloud-route sample of 10 ru and 10 sk gold queries was run and semantically reviewed as recorded below. The private cloud artifact exists and its SHA-256 matches the recorded value. T011 is `done`.

Acceptance retains the measured limitations: the cloud sample has 19 passes and one surname-transliteration caveat (`q002/ru`); the separate local-model sample has two semantic failures (`q004/sk`, `q005/sk`). These observations do not establish a code or prompt fix, full-set translation quality, retrieval quality, or answer-generation quality. Earlier statements that T011 remains pending acceptance are historical checkpoints superseded by this acceptance record.

### Verification checkpoint before acceptance — 2026-11-19

**T011-VERIFY-01 checked:** following the user's explicit authorization to use the paid DeepSeek API, the cloud-route review of 10 ru and 10 sk gold-set translations is complete. Acceptance criterion 2 is verified for this sample. T010 has been accepted by the user. This checkpoint preceded the T011 acceptance recorded above.

Ran `q001`–`q010` in ru and sk, the same selection and gold-file SHA-256 as the prior local run, through unchanged `create_chat_client(..., route="cloud")` and `translate_query`. Configured and API-reported model: `deepseek-flash`; provider: DeepSeek; prompt: `query-translation-v1`; thinking disabled; `temperature=0.0`; `max_tokens=512`. The harness bounded the run to 20 requests and set retries to zero on its in-memory client only. Exactly **20 HTTP attempts succeeded with HTTP 200**, without retries, request errors, or additional paid calls. No source, prompt, or persistent configuration change was needed.

**Cloud format and language checks:** 20/20 passed the existing strict response parser, reported the expected ru/sk language, and ended with `stop`. **Manual semantic review:** comparison of every original query, its paired English gold formulation, and the generated translation found **19 pass, 1 pass with caveat, 0 fail**. The caveat is `q002/ru`: the question's meaning is preserved, but the author surname is transliterated differently from the paired English reference, which may affect name-sensitive retrieval. The remaining cases preserve source meaning and retrieval-relevant terms, including `q004/sk` and `q005/sk`, which failed in the separate local-model run. These provider-specific observations do not establish a code or prompt fix or a full-set quality estimate.

The private per-case record is `data/eval/T011-deepseek-verification-20261119T202223Z-814c0bdb.json` (SHA-256: `1d36c5a6bbc1a3c7014de42e8e5d90eb11178e92790de59c30a1437e7d1b681f`). The destination was verified Git-ignored and created exclusively before any request, so no pre-existing artifact was overwritten. It records the gold-file hash, route/model/prompt, all 20 original/gold/response records, individual semantic verdicts, attempts, and usage. It contains private query material and must remain outside Git.

The artifact's statement that gold-label review remains pending is stale: the user explicitly accepted T010. Whether the user marked or reviewed each individual entry was not independently established. The artifact is retained unchanged as execution evidence.

API-reported usage: **4,765 input tokens**, all cache misses, and **528 output tokens**, **5,293 total**. Using the [official DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/) checked on 2026-11-19, the published off-peak rates at the run's approximately 20:22 UTC time produce an **estimated cost of USD 0.00103155** (USD 0.15 per million cache-miss input tokens and USD 0.60 per million output tokens). This is a pricing-based estimate, **not a verified actual charge**: the response reports token usage without a charge field; no balance or transaction endpoint was called.

The earlier local results and cloud-pending statements below are historical checkpoints superseded by this cloud review. The local model's two semantic failures remain recorded as local evidence. Retrieval and answer-generation quality were not evaluated in this check.

The four T006 defects driving the original report's verdict have since been fixed and independently reviewed; see the [resolution addendum](../docs/reviews/T006-T011-2026-11-19.md#resolution-addendum--2026-11-19). An additional source-change race fix is implemented with passing focused regressions and a final full fast-suite result of 694 passed, 1 deselected. Earlier review snapshots and counts below remain historical evidence.

### Earlier local model verification — 2026-11-19

Ran the first 10 gold records (`q001`–`q010`), each in ru and sk, through unchanged `translate_query` and `create_chat_client(..., route="local")`. Model: existing `Qwen_Qwen3.5-9B-IQ4_XS.gguf`; prompt: `query-translation-v1`; `temperature=0.0`, `max_tokens=512`, no client retry. An inline Python harness started the existing llama-server hidden on a dedicated loopback port with the ADR 0001 settings (`-ngl 99 -fa on -c 16384 --parallel 1 -ub 256 -b 1024 --jinja`), then terminated and waited for only its owned subprocess. No download, purchase, source/configuration change, or cloud generation call was made.

**Verified locally:** 20/20 responses passed the strict response parser and reported the expected language. Manual comparison of each original query, its paired gold English formulation, and the generated translation found **15 pass, 3 pass with caveat, 2 fail**:

- `q004/sk` — fail: changes the domain-specific treatment relationship and leaves a word untranslated, losing the named treatment and changing the meaning.
- `q005/sk` — fail: omits the systematic review context and changes the subject to the addressee.
- `q002/ru`, `q004/ru`, `q007/ru` — pass with caveat: preserve the main question but have proper-name transliteration or domain-term fidelity issues that may affect retrieval.

The ignored local artifact `data/eval/T011-local-verification-2026-11-19.json` records the gold-file SHA-256, model/route/prompt, all 20 pairs and individual review verdicts, and owned-server cleanup. It contains private query content and must remain outside Git. Its destination was checked as Git-ignored before writing; whether a prior artifact already existed at that path was **not checked**, so absence of overwritten prior data cannot be established. This is a limited sample, not a full-set quality estimate.

These results demonstrate semantic translation failures in this local model run; they do not isolate a confirmed code or prompt defect or establish an effective fix. The existing parser checks format and plausibility, not full semantic equivalence. The prompt already requires meaning preservation. No prompt or parser change, or repeated generation attempt, was justified or performed on this evidence alone.

**Historical cloud limitation at the local-run checkpoint (superseded above):** acceptance criterion 2 still required the cloud-route review. The configured DeepSeek API has nonzero token pricing ([official pricing](https://api-docs.deepseek.com/quick_start/pricing/)), so it was not used under the user's zero-provider-cost requirement. OpenRouter offers zero-priced `:free` models without a credit purchase ([official free-model collection](https://openrouter.ai/collections/free-models/)); live public metadata showed `google/gemma-4-31b-it:free` at zero input/output pricing, but no OpenRouter key is available through `load_secrets()`. Account eligibility and compatibility with the existing ZDR/data-collection restrictions remain unverified. This alternative model would not establish behavior of configured DeepSeek. T011 remains `review`, without acceptance.

### Historical independent review handoff — 2026-11-19

The later [review of all uncommitted changes](../docs/reviews/T006-T011-2026-11-19.md) found **no new confirmed material defect in T011**. The focused isolated run passed **119 tests with `-W error`**; the whole reviewed working tree passed **661 tests, 1 deselected**. These results support criterion 1 but do not establish real-cloud translation quality or protocol compliance.

**T011-VERIFY-01 remains open:** acceptance criterion 2 requires the recorded review of 10 ru and 10 sk gold-query translations through the cloud route. This is a verification gap, not a confirmed implementation defect. Status remains `review`, without acceptance. The report's overall **Changes required** verdict is driven by the four open T006 defects; the user requested the report be saved for a separately requested fixing session. The implementation/review accounts below are historical evidence and do not close criterion 2.

Implemented by a Tier 2 executor (Sonnet 5.5, high effort). Proposed status: `review`; acceptance criterion 2 is pending.

### What was done

- `translate_query(query, client) -> TranslatedQuery` in `src/ragshelf/retrieve/translate.py`; `TranslatedQuery` is a frozen dataclass: `original`, `english`, `language` (lowercase two-letter ISO 639-1), `translated` (False for pass-through), `prompt_version`, `model`, `route`.
- Versioned prompt in `src/ragshelf/prompts/query_translation.py` (`PROMPT_VERSION = "query-translation-v1"`; change the text only with the version). The system message holds the rules; the query goes into the user message as `<query>…</query>`, and any query tag in the query text (`</query>` or `<query>`, in any case, with whitespace inside the tag such as `</query >` or `< /query>`) gets a backslash after its `<`, so the query can neither close nor reopen the block. The model is told the query is data, never instructions.
- One `ChatClient.complete` call per query (`temperature=0.0`, `max_tokens=512`), no retry. The model answers in a strict two-line format: `language: <code>` / `translation: <English, one line>`. Works with any `ChatClient`, cloud or local.
- Failures raise `TranslationError` (a subclass of `LLMError`): blank query; `LLMError` from the client (wrapped, cause kept); `finish_reason == "length"` (reported as cut off) or any other value except none or `stop` (`content_filter`, `insufficient_system_resource`, ...; reported as an abnormal end); reply not in the two-line format (blank lines are ignored; multi-line commentary, missing or empty translation, bad language code: exactly two letters are accepted, a region suffix such as `ru-RU` is dropped to `ru`, three-letter codes such as `rus` and words raise); translation longer than 4x the query + 100 characters; translation without letters or mostly Cyrillic (not translated); a translation identical to the query ignoring case, spacing and punctuation (echo), except the short no-op below; a translation that repeats the `translation:` label or starts or ends with a stray quote or markup character that the query does not have (quote characters `"`, `“ ” „`, `« »` are one family: a quote at the edge is stray only when the query contains no quote character at all; backtick, `*` and `_` are stray unless the query has that same character); the model reporting `en` for a query whose letters are mostly Cyrillic (more than half, the same rule as for translations; an English query quoting one Russian term passes through). The original query is never returned as a fallback.
- Symmetric wrappers the model puts around the translation (quotes, guillemets, backticks, `**`, `__`, `*`, `_`, nested) are stripped only when they enclose the whole text (the inner text does not contain the opener or closer again); a quote wrapper is kept when the query itself starts with any quote character (so `«phrase»` translated to `"phrase"` is returned with its quotes). Converting guillemets or typographic quotes to straight quotes is accepted and returned intact, including several separately quoted phrases (`«a» и «b»` -> `"a" and "b"`). Separately emphasised phrases with backtick, `*` or `_` (`_x and _y_`) are not "repaired": the stray edge character raises unless the query contains that character, in which case the text is returned untouched.
- English queries return `english` equal to the query with surrounding whitespace stripped (`original` stays exactly as given); the model's `translation` line is ignored for `en`.
- No-op: if the translation equals the query after normalisation and the query is short (at most 3 whitespace-separated words) and has no Cyrillic (`Bratislava` labelled `sk`, `Python` labelled `ru`), it is accepted as `translated=False`, `english` = the stripped query, `language` = the model's label. A longer query, or any query containing Cyrillic, returned unchanged still raises.

### Files

- `src/ragshelf/retrieve/__init__.py`, `src/ragshelf/retrieve/translate.py`
- `src/ragshelf/prompts/__init__.py`, `src/ragshelf/prompts/query_translation.py`
- `tests/retrieve/test_translate.py` (119 test cases; no package files needed under `tests/`, the suite uses `--import-mode=importlib`)

### Review fixes

Three findings of an independent review were applied: (1) the language code is exactly two letters (region suffix dropped, three-letter codes rejected); (2) the Cyrillic check for an `en` verdict raises only when Cyrillic letters are the majority, the same >0.5 rule as for translations; (3) the query delimiter is protected against tag variants and an opening `<query>`. The prompt text is unchanged, so `PROMPT_VERSION` stays `query-translation-v1`; only the escaping of queries that contain such tags differs.

A second independent review led to five more changes (P2: quote characters treated as one family; a short Latin-script query identical to the translation is a no-op; P3: blank lines between the reply lines are ignored; any `finish_reason` other than none or `stop` raises; pass-through `english` is the stripped query). The prompt text is unchanged, so `PROMPT_VERSION` stays `query-translation-v1`.

### Language detection choice

Detection is done by the LLM in the same call as the translation, not by a detector. Reasons: no extra request; no new dependency; works for short and code-mixed queries (a query in Russian or Slovak with English acronyms is classified by its main text, which a character-statistics detector does poorly); the translation call needs the model's judgment of "already English" anyway. `langdetect` is already in `pyproject.toml` but was not used: it is unreliable on very short queries and on mixed text, and is non-deterministic unless seeded. Cost: every query, English included, costs one LLM call. The only non-LLM rule is the Cyrillic sanity check above, which guards the pass-through path against a wrong `en` answer.

### Checks

- `venv/Scripts/python.exe -m pytest tests/retrieve/test_translate.py -p no:cacheprovider` — verified: 119 passed (also clean with `-W error`).
- Full fast suite — **661 passed, 1 deselected** on 2026-11-19 (orchestrator run on the whole working tree, which also contains the T006 work; 124 before T011). `tests/retrieve` alone: 119 passed, also with `-W error`.
- Acceptance criterion 1 (scripted-client tests for ru, sk, en pass-through, failure) — verified, plus short queries, mixed Russian/Slovak with English terms, prompt-injection-like query (delimiting, and an obeying reply raises), local-route client, deterministic settings.
- Acceptance criterion 2 (review of 10 ru and 10 sk gold-set translations through the cloud route) — not verified; no real LLM call was made in this work. The gold set now exists (see the current checkpoint above). The future check needs: 10 ru and 10 sk queries selected from that set, a configured cloud client (`create_chat_client`, key in `.env`), a run of `translate_query` over those 20 queries, and a reviewer's verdict per pair (original, `english`, `language`) recorded here. Also confirm there that the model follows the two-line format without thinking text on both routes.

### Limitations

- The prompt and parser were exercised only against scripted replies, not a real model: real-model format compliance (for example thinking text or code fences, which are deliberately not tolerated) is unproven until criterion 2. Quote and emphasis wrappers are handled (stripped or rejected) and tested only with scripted replies. A reply wrapped in single quotes whose text contains an apostrophe (`'don't stop'`) is no longer stripped and keeps its quotes, because `'` is not in the stray-markup set. The only finish reasons accepted are none and `stop`; a provider that reports a different normal end value would fail until it is added.
- A wrong `en` for a Latin-script non-English query (Slovak without diacritics, transliterated Russian) passes through untranslated; only a mostly Cyrillic query is caught by the sanity check, so a Russian query with more than half of its letters in Latin script labelled `en` also passes through. A test pins this so a future change is deliberate.
- Echo detection is exact after normalising case, spacing and punctuation. A Latin-script query returned with only a few words changed, or lightly paraphrased without being translated, is not detected. A query of more than 3 words that is only identifiers or English terms but labelled non-English by the model raises as an echo (a short one is accepted as a no-op), and so does any echo of a query with Cyrillic. The no-op rule also accepts a model that merely failed to translate a short Latin-script query; that cannot be told apart from a genuine no-op.
- Very long queries are sent as is, with no truncation or length check; one longer than the model's context fails as an `LLMError` (wrapped as `TranslationError`) or gives a cut-off reply. Not handled; documented limitation.
- Multi-line queries are sent as is; the translation must still be a single line.
- Package naming: this task area is `retrieve/`; the prototype package `src/ragshelf/retrieval/` (reranker) is a different spelling and was not touched. The orchestrator should decide whether the two should be unified.

### Status and independent review — 2026-11-18

T011 is `review`. Started because its only dependency, T004, is `done`; T005 (still in `review`) is not a dependency. Independent read-only reviews (Tier 2, Sonnet 5.5 / high, requested settings; execution settings not exposed) ran in three rounds and the findings above were fixed. The orchestrator re-ran the full fast suite after the last fix: **218 passed, 1 deselected**. `src/ragshelf/retrieve/__init__.py` was added to `area` as the package file the layout requires; it is shared with T012/T013, which may extend it. The existing prototype package `src/ragshelf/retrieval/` (reranker) uses a different spelling; unifying the names is left to the owner of the reranker task (T013). Criterion 2 is **not verified** (blocked on the T010 gold set); user acceptance is pending and T011 must not move to `done` before criterion 2 is checked or the user explicitly accepts without it.
