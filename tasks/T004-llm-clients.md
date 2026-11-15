---
id: T004
title: Replace the LLM client with cloud and local clients
milestone: M1
status: planned
depends_on: [T003]
area:
  - "src/ragshelf/llm/**"
  - "src/ragshelf/generation/rag_chain.py"
  - "src/ragshelf/retrieval/reranker.py"
  - ".env.example"
  - "tests/llm/**"
  - "tests/fakes.py"
  - "docs/decisions/0001-model-stack.md"
---

# T004 — Replace the LLM client with cloud and local clients

## Goal

Give the pipeline one chat interface with an OpenRouter client and a llama-server client that fail loudly, and confirm both against the real endpoints.

## Sources

- [Generation rows in ADR 0001](../docs/decisions/0001-model-stack.md)
- [Configuration in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: A `ChatClient` protocol (`complete(messages, max_tokens, temperature) -> Completion` with text, model, route, token usage). OpenRouter client with the ADR 0001 provider settings and `reasoning.effort = "none"`, request timeout, retries with backoff on 429 and 5xx, and an `LLMError` on failure instead of answer text. llama-server client for the OpenAI-compatible endpoint with thinking disabled. Key read from `OPENROUTER_API_KEY` (rename in `.env.example`). A scripted fake client in `tests/fakes.py`. Switch the two existing callers to the new client; delete `llm/deepseek_llm.py`. Record the first real request in ADR 0001 "Consequences".

Out of scope: Starting or stopping `llama-server` from code (T013). Prompt design (T011, T017).

## Acceptance Criteria

1. Unit tests with a mocked HTTP layer cover success, a retried 429, a non-retried 400, a timeout, and an error raised as `LLMError`.
2. A real cloud request with a Russian question returns a non-empty answer; model, route, and token usage are recorded in the Result.
3. A real request to `llama-server` started with the ADR 0001 command returns a non-empty answer.
4. No module references `DEEPSEEK_API_KEY` or `deepseek_llm`.

## Checks

- `venv/Scripts/python.exe -m pytest tests/llm`
- Manual: a one-off call through each client, output recorded in Result (no key printed).
- `git grep -n "DEEPSEEK_API_KEY\|deepseek_llm" -- src scripts .env.example` prints nothing.

## Open Questions

- The user adds `OPENROUTER_API_KEY` to `.env` (STATUS "Pending setup").

## Result

Not started.
