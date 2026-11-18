---
id: T004
title: Replace the LLM client with cloud and local clients
milestone: M1
status: done
depends_on: [T003]
area:
  - "src/ragshelf/llm/**"
  - "src/ragshelf/app/streamlit_app.py"
  - "src/ragshelf/config.py"
  - "src/ragshelf/__main__.py"
  - "src/ragshelf/generation/rag_chain.py"
  - "src/ragshelf/retrieval/reranker.py"
  - ".env.example"
  - ".gitignore"
  - "AGENTS.md"
  - "README.md"
  - "ROADMAP.md"
  - "STATUS.md"
  - "pyproject.toml"
  - "ragshelf.toml"
  - "tests/llm/**"
  - "tests/fakes.py"
  - "tests/conftest.py"
  - "tests/test_app_startup.py"
  - "tests/test_config.py"
  - "tests/test_cli.py"
  - "docs/decisions/0001-model-stack.md"
  - "docs/decisions/0003-deepseek-platform-cloud-route.md"
  - "docs/reviews/T004-2026-11-16.md"
  - "data/README.md"
  - "docs/data-layout.md"
  - "tasks/T004-llm-clients.md"
  - "tasks/T005-document-scan-and-parse-cache.md"
  - "tasks/T009-ingest-command.md"
  - "tasks/T014-query-tracing.md"
  - "tasks/T021-final-cleanup.md"
---

# T004 — Replace the LLM client with cloud and local clients

## Goal

Give the pipeline one chat interface with an OpenRouter client and a llama-server client that fail loudly, and confirm both against the real endpoints.

## Sources

- [Generation rows in ADR 0001](../docs/decisions/0001-model-stack.md)
- [Configuration in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [ADR 0003: DeepSeek platform as the default cloud route](../docs/decisions/0003-deepseek-platform-cloud-route.md) (added during the task, see the planning change below)

## Scope

In scope: A `ChatClient` protocol (`complete(messages, max_tokens, temperature) -> Completion` with text, model, route, token usage). OpenRouter client with the ADR 0001 provider settings and `reasoning.effort = "none"`, request timeout, retries with backoff on 429 and 5xx, and an `LLMError` on failure instead of answer text. llama-server client for the OpenAI-compatible endpoint with thinking disabled. Key read from `OPENROUTER_API_KEY` (rename in `.env.example`). A scripted fake client in `tests/fakes.py`. Switch the two existing callers to the new client; delete `llm/deepseek_llm.py`. Record the first real request in ADR 0001 "Consequences".

Out of scope: Starting or stopping `llama-server` from code (T013). Prompt design (T011, T017).

## Acceptance Criteria

1. Unit tests with a mocked HTTP layer cover success, a retried 429, a non-retried 400, a timeout, and an error raised as `LLMError`.
2. A real cloud request with a Russian question, sent through the default cloud provider (the DeepSeek platform), returns a non-empty answer; model, route, and token usage are recorded in the Result.
3. A real request to `llama-server` started with the ADR 0001 command returns a non-empty answer.
4. No module references `deepseek_llm`, and no module reads a key itself with `os.getenv` or `load_dotenv`. `DEEPSEEK_API_KEY` names only the DeepSeek platform key, loaded by `load_secrets()`.

Planning change (2026-11-16), decided by the user during the task: OpenRouter will not be used for now but stays in the code; the cloud route goes to the DeepSeek platform with the user's own key. The decision is recorded in ADR 0003. Effects on this task:

- Scope: a DeepSeek platform client and a `llm.cloud_provider` setting are added; the OpenRouter client stays, with unit tests only. `llm.cloud` from T003 is split into `llm.deepseek` and `llm.openrouter`, and `Secrets` gains `deepseek_api_key`.
- Criterion 2 originally read "A real cloud request with a Russian question returns a non-empty answer; model, route, and token usage are recorded in the Result." It now names the provider.
- Criterion 4 originally read "No module references `DEEPSEEK_API_KEY` or `deepseek_llm`." That name is now the DeepSeek platform's key variable, so the criterion keeps its intent: the prototype client and its ad-hoc key reading are gone.
- The real OpenRouter request is no longer part of this task.
- Dependent tasks are unaffected: they use the cloud route through `create_chat_client`.

Review follow-up (2026-11-17): the `area` now includes the provider split and ancillary fixes already described in Result, the application-startup regression fix and test, and the user-decided relocation of the data-layout documentation to `docs/data-layout.md`. The original review is retained at `docs/reviews/T004-2026-11-16.md`. No acceptance criterion changed. Planned tasks that maintain the data-layout document now name its new path; their implementation remains unstarted.

## Checks

- `venv/Scripts/python.exe -B -m pytest tests/test_app_startup.py -p no:cacheprovider` (offline fresh-process application import; no model loading or credential access).
- `venv/Scripts/python.exe -m pytest tests/llm`
- Manual: a one-off call through the default cloud client and the local client, output recorded in Result (no key printed).
- `rg -n 'deepseek_llm|load_dotenv|getenv' src .env.example` returns no matches (expected exit code 1; includes untracked files).

## Open Questions

None.

## Result

### Acceptance — 2026-11-17

The user accepted T004 on 2026-11-17 and instructed continuation with T005. The acceptance closes T004 as `done`; the recorded M1 exit criteria are met, and work continues in M2. The rework and original review evidence below remain dated history. Acceptance does not authorize a push or the T005 data migration.

### Rework result — 2026-11-17

The two findings and the user-decided follow-up from the [original independent review](../docs/reviews/T004-2026-11-16.md) are resolved. That report is preserved as the dated findings snapshot; this section records the subsequent resolution evidence. At the end of the rework, T004 remained `review`, committed locally but awaiting user acceptance; M1 was not yet accepted. The later acceptance above supersedes that status.

| ID | Resolution and verification |
| --- | --- |
| T004-REV-01 | `streamlit_app.py` now calls `apply_environment(load_settings())` at the application boundary before Streamlit or any transitive model-library import. `tests/test_app_startup.py` imports the actual application in a fresh process after clearing HF, Hugging Face, Transformers, MinerU, Ragshelf, and provider-key variables. It enables HF/Transformers offline mode, rejects network/DNS events, blocks `from_pretrained()` calls, and forbids `load_secrets()`. It asserts imported Hugging Face cache constants, the HF telemetry opt-out, and MinerU environment values. Before the fix: **1 failed**, with `HF cache is outside the project`; after the fix: **1 passed in 8.75 s**. An independent read-only review reran it: **1 passed in 11.08 s**, with no supported findings. The CLI and guarded `__main__` remain standard-library placeholder paths; no other affected runtime boundary required initialization. |
| T004-REV-02 | The `area` now contains **30 patterns**, covering all **38 changed/new/deleted paths**, including provider/configuration changes, ancillary code and documentation, and this rework. The existing planning-change explanation is retained. `data/README.md` is intentionally included for its deletion. |
| T004-FOLLOWUP-01 | Moved `data/README.md` to [docs/data-layout.md](../docs/data-layout.md). Its content and layout table are preserved except for the opening paragraph, updated to describe the relocated documentation and the full data-directory ignore rule. Active AGENTS/README links and the areas of T005, T009, T014, and T021 name the new path; completed-task history is preserved. `/data/` is fully ignored, with no README exception. Content preservation, active links, and ignore matching were checked. No library data or model files were moved. |

Current verification (2026-11-17):

| Check | Result |
| --- | --- |
| `venv/Scripts/python.exe -B -m pytest -p no:cacheprovider` | **96 passed** |
| `venv/Scripts/python.exe -B -m pytest tests/llm -p no:cacheprovider` | **65 passed** |
| `venv/Scripts/python.exe -m pip check` | `No broken requirements found.` |
| `venv/Scripts/ragshelf.exe --help` | Lists `ingest`, `search`, `ask`, and `eval` |
| Package import walk excluding `ragshelf.app`, after explicit `apply_environment(load_settings())` with `HF_HUB_OFFLINE=1` | **23 modules**, successful; known `fitz` deprecation warning. This checks compatibility; the fresh-process application test above establishes startup initialization. |
| `rg -n 'deepseek_llm|load_dotenv|getenv' src .env.example` | No matches; expected exit 1 |
| `git diff HEAD --check` | Exit 0; line-ending conversion warnings only |
| `git check-ignore --no-index data/README.md data/example-untracked.txt data/library/example.pdf` | All three match `/data/` |
| `git ls-files data models .python .tools venv .env` | The pre-staging rework check still listed only `data/README.md`; after authorized staging, the protected-path query returns no files. |

At the end of the rework session, no files had been staged and no commit or push had been performed. The subsequent local T004 commit stages the README relocation and removes the old README from the index; it has not been pushed.

Delegation: the import-ordering review was requested at **Tier 4, GPT-6 Astra / high**, because library import ordering affects cache initialization. Mechanical verification and the documentation relocation were requested at **Tier 1, GPT-6 Luna / max**, using specified commands and replacements. This bounded task/status record update was requested at **Tier 2, GPT-6.1 Sol / medium**, with the contract and check results supplied. The main agent inspected the resulting files/diffs and integrated the source, regression test, and area changes. Actual execution settings and token metrics were not exposed and are not claimed; the test durations above are reported check results, not total worker time.

Limitations: no new live cloud or local-model request was made in this rework session; the successful live requests in the original review remain evidence dated 2026-11-16. The new test verifies bare application import, cache selection, and telemetry opt-out state; it does not exercise a full Streamlit server, PDF processing, model download, or actual telemetry transmission. OpenRouter's live endpoint remains unverified. At the end of the rework, T005 still required M1 acceptance and confirmation of the data migration. M1 acceptance is now recorded above; the migration remains subject to separate user confirmation.

### Earlier implementation and review record

The following account is preserved as the implementation history. Its earlier closure statements do not supersede the acceptance and rework record above; historical executions are not treated as independent evidence by the dated review.

What was done:

- `src/ragshelf/llm/base.py`: `ChatClient` protocol, `Message`, `Usage`, `Completion` (text, model, route, usage, and `finish_reason`), `LLMError`.
- `src/ragshelf/llm/openai_compatible.py`: shared client for OpenAI-compatible endpoints. Request timeout; retries only on HTTP 429 and 5xx with exponential backoff (1 s, 2 s, 4 s, …, a numeric `Retry-After` honoured, each wait capped at 30 s); every other failure raises `LLMError` at once. A 200 response raises `LLMError` when it carries an error object (top-level or on the choice), `finish_reason: "error"`, no content, empty content, or a non-JSON body. API keys are validated on construction and redacted from every error message.
- `src/ragshelf/llm/deepseek.py`: DeepSeek platform client, the default cloud provider (ADR 0003): `thinking: {"type": "disabled"}`.
- `src/ragshelf/llm/openrouter.py`: OpenRouter client with `reasoning.effort = "none"` and the ADR 0001 `provider` settings. Unit-tested only.
- `src/ragshelf/llm/llama_server.py`: local client, `chat_template_kwargs.enable_thinking = false`, no credentials.
- `src/ragshelf/llm/__init__.py`: `create_chat_client(settings, secrets=None, route=None, cloud_provider=None)`; raises `LLMError` when the chosen cloud provider has no key.
- `src/ragshelf/config.py` (from T003): `llm.cloud` split into `llm.deepseek` and `llm.openrouter`; `llm.cloud_provider` added (default `deepseek`); `Secrets.deepseek_api_key` added. `ragshelf.toml` and `tests/test_config.py` follow.
- `tests/fakes.py`: `ScriptedChatClient`. `tests/llm/`: fake HTTP session and 65 tests. `tests/conftest.py`: clears `RAGSHELF_*` and both key variables for every test.
- Callers: `generation/rag_chain.py` and `retrieval/reranker.py` use `create_chat_client`; `generate_paragraph` takes an optional `client`. `llm/deepseek_llm.py` is deleted. Nothing calls `load_dotenv` any more.
- `.env.example`: `DEEPSEEK_API_KEY` (DeepSeek platform) and `OPENROUTER_API_KEY`.
- ADR 0003 (new): the cloud-route decision. ADR 0001: the two "Where it lives" cells, the key bullet, and a Consequences bullet with the first real local request. README, STATUS.

Changes outside the task's `area`, and why:

- `pyproject.toml`: pytest `pythonpath = ["tests"]` so tests can `from fakes import …`; `python-dotenv` removed from the direct dependencies because no module imports it now (it stays installed as a dependency of `pydantic-settings`).
- `src/ragshelf/__main__.py`, `tests/test_cli.py`: a T002 defect found here. `__main__.py` ran the CLI on import, so the package import walk used as a check in T001 exited with code 2. It is now guarded by `if __name__ == "__main__":`, with a test.
- `src/ragshelf/config.py`, `ragshelf.toml`, `tests/test_config.py`, `tests/conftest.py`, `docs/decisions/0003-…`: the planning change above.

Behavior changes in the callers beyond "errors now raise" (prompt design stays with T011 and T017; both modules are deleted by later tasks):

- `generate_paragraph` now sends `max_tokens=1500, temperature=0.3`; the prototype sent neither.
- The LLM reranker now sends `max_tokens=200, temperature=0.0` and no system message; the prototype client added its "Ты научный ассистент…" system prompt to every call.
- The prototype's optional `HTTP-Referer` and `X-Title: ragshelf` headers are no longer sent, so the project name does not go to an outside service.

Checks (run by the main agent and subagents):

| Criterion | Check | Outcome |
| --- | --- | --- |
| 1 | `venv/Scripts/python.exe -m pytest tests/llm`: 65 passed. Covers success, a retried 429, a non-retried 400, a timeout, failures raised as `LLMError`, and the review regressions described below, against a fake HTTP session | verified |
| 2 | Real request through `create_chat_client(load_settings(), load_secrets(), route='cloud').complete([{'role': 'user', 'content': 'Что такое RAG? Ответь по-русски двумя короткими предложениями.'}], max_tokens=200, temperature=0.2)`: model `deepseek-flash`, route `cloud`, 22 prompt + 76 completion = 98 total tokens, `finish_reason: stop`; returned a non-empty, correct two-sentence Russian explanation of RAG | verified |
| 3 | `llama-server` started with the ADR 0001 command. The first request through `LlamaServerClient` returned a correct two-sentence Russian answer without thinking text: model `Qwen_Qwen3.5-9B-IQ4_XS.gguf`, route `local`, 50 prompt + 70 completion tokens, 2.9 s; VRAM was 5,865 of 6,144 MiB. Fresh retest through `create_chat_client(load_settings(), route='local')` with the same Russian question and `max_tokens=200, temperature=0.2` returned a non-empty, correct two-sentence Russian answer without thinking text: model `models/gguf/Qwen_Qwen3.5-9B-IQ4_XS.gguf`, route `local`, 29 prompt + 63 completion = 92 total tokens, `finish_reason: stop`, 3.23 s. The server was then stopped; its process was absent and port 8081 was free | verified |
| 4 | `rg -n 'deepseek_llm|load_dotenv|getenv' src .env.example` | verified: no matches (expected exit code 1; the search includes untracked files) |

Also checked: the full suite, `venv/Scripts/python.exe -m pytest` → 95 passed; the 23-module package import walk exits 0 (with a `fitz` deprecation warning); `ragshelf --help` lists `ingest`, `search`, `ask`, and `eval`; `pip check` reports no broken requirements. The earlier T004 check found `pip freeze --all` matched `requirements.txt` except the editable `ragshelf` entry; it was not repeated in this session. A credential scan of 26 changed or new files passed; real values were compared locally and never printed. `git diff --check` passed.

Independent review: read-only, by a separate subagent with fresh context (tier 3, preset `opus-high`: Opus, high effort; the tool does not report the executed parameters; it reported 121,195 subagent tokens and 219 s, the worker's usage only). It reviewed the state before the DeepSeek client was added. Verdict: changes required, one major and four minor findings, all addressed:

| Finding | Resolution |
| --- | --- |
| F1 (major): a key containing a newline made `requests` raise `InvalidHeader`, whose text quotes the whole `Authorization` value, and that text went into the `LLMError` message and its chained cause | Keys are validated on construction (printable ASCII, no whitespace) with an error that does not echo the value; the key is redacted from every message built from an exception or a response body; a cause that quotes the key is not chained. Tests added, including one with a real `requests.Session` |
| F2 (minor): a 200 response with a choice-level error or `finish_reason: "error"` came back as answer text; a truncated answer could not be told apart | Both error forms raise `LLMError`. `Completion.finish_reason` exposes `"length"`; the caller decides (T017) |
| F3 (minor): a malformed `usage` raised `AttributeError`; `model` was not type-checked | Both fall back: empty `Usage`, configured model name. Tests added |
| F4 (minor): the caller switch added literal request parameters | Recorded above as intentional |
| F5 (minor): documents disagreed on where settings live | ADR 0001, `.env.example`, `ragshelf.toml`, and STATUS now say: defaults in `src/ragshelf/config.py`, overridable in `ragshelf.toml` |

The DeepSeek client, provider setting, and fixes above were written after that first review. A second read-only independent review, requested at Tier 4 (GPT-6 Astra, high), found two P2 error-path issues; the review tool did not report actual runtime model or effort settings, or worker metrics:

| Finding | Resolution |
| --- | --- |
| R1 (P2): raw timeout details and nested exception chains could expose a synthetic key in a traceback | Transport and parse catches now raise from `None`, while retaining sanitized transport detail in the `LLMError` message |
| R2 (P2): truncating error text before redaction could expose a synthetic key prefix when the key crossed the 500-character boundary | Redaction now runs on the full text before the 500-character limit is applied |

Ten regression tests were added (six transport-traceback cases, three error-location boundary cases, and one `JSONDecodeError` case); the existing ordinary-error contract was updated. The targeted tests had 9 failures and 1 pass before the fixes, then 11 passed after. The final independent review reported all 65 LLM tests passing and no remaining supported defects. The credential scan covered the 26 changed or new files and passed without printing values.

Mechanical verification, the local server launch, and documentation updates were delegated at Tier 1, requesting GPT-6 Luna with max effort, because the commands and replacements were specified. The main agent performed the live cloud and local requests, local cleanup, the security fixes, and final integration. The tools did not expose actual execution settings or usage metrics for these workers.

Limitations:

- The OpenRouter client has never been run against the real endpoint.
- `Reranker(method="llm")` and the default-client path of `generate_paragraph` have no tests; the Streamlit app was not run.
