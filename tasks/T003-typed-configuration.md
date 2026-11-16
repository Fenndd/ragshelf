---
id: T003
title: Add typed configuration
milestone: M1
status: done
depends_on: [T002]
area:
  - "src/ragshelf/config.py"
  - "ragshelf.toml"
  - "tests/test_config.py"
  - "pyproject.toml"
  - "requirements.txt"
  - ".env.example"
  - "README.md"
---

# T003 — Add typed configuration

## Goal

Replace hardcoded paths, model names, and parameters with one typed configuration whose hash identifies a pipeline setup.

## Sources

- [Configuration in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Model stack (values to carry over)](../docs/decisions/0001-model-stack.md)

## Scope

In scope: `config.py` with pydantic-settings: sections for paths (`data/library`, `data/cache`, `data/index`, `data/traces`, `data/eval`, `models/`), models (paths and IDs from ADR 0001), chunking, retrieval (top-k values, RRF k, rerank depth, context N), LLM routes (cloud model, provider preferences, local server URL, timeouts). Loaded from `ragshelf.toml`, overridden by `RAGSHELF_*` environment variables; secrets from `.env` only. A function returning a stable hash of the non-secret settings. A function that sets `HF_HOME`, `MINERU_HOME`, and the telemetry variables before model libraries import. Paths resolve relative to the repository root regardless of the working directory.

Out of scope: Using the configuration in existing modules (each later task switches its own module).

## Acceptance Criteria

1. Loading with no `ragshelf.toml` overrides yields the ADR 0001 / ADR 0002 defaults.
2. An environment variable overrides a TOML value.
3. The hash is identical for two loads of the same settings and differs when any non-secret value changes; secrets appear neither in the hash input nor in `repr`.
4. Paths resolve to the same absolute locations when the process starts in another directory.

## Checks

- `venv/Scripts/python.exe -m pytest tests/test_config.py`

## Open Questions

None

## Result

Accepted by the user 2026-11-16 and committed as one commit. Done in the main session; nothing was delegated.

What was done:

- `src/ragshelf/config.py`: `Settings` (pydantic-settings) with sections `paths`, `models`, `chunking`, `retrieval`, and `llm` (`route`, `cloud`, `local`). Sources in order of precedence: `RAGSHELF_<SECTION>__<KEY>` environment variables, `ragshelf.toml`, defaults. Unknown keys and out-of-range values are validation errors; settings are immutable. Functions: `load_settings(toml_file=None)`, `load_secrets(env_file=None)`, `config_hash(settings)`, `hash_input(settings)`, `apply_environment(settings)`.
- Paths: every `Path` field is resolved against the repository root (found from the module's location), so results do not depend on the working directory. The hash input writes paths under the repository root as relative POSIX paths, so the hash does not depend on where the checkout lives.
- Secrets: a separate `Secrets` class holds `openrouter_api_key` as a masked `SecretStr`, read from the process environment or `.env`. It is not part of `Settings`, so it cannot reach the hash, and `Settings` rejects such a key in `ragshelf.toml`. An empty value counts as not set.
- `apply_environment` sets `HF_HOME`, `MINERU_HOME`, `HF_HUB_DISABLE_TELEMETRY`, and `MINERU_TELEMETRY_DISABLED`. Importing `ragshelf.config` loads no model library.
- `ragshelf.toml`: every key, commented out, with its default.
- `tests/test_config.py`: 16 tests.
- `pyproject.toml`: `pydantic` and `pydantic-settings` added as direct dependencies. `venv/`: installed `pydantic-settings 2.16.3` (no other package changed); `requirements.txt` has the pin.
- `.env.example`: notes on where settings and secrets live. The key is still named `DEEPSEEK_API_KEY` there; T004 renames it.
- `README.md`: section "Configuration" and a layout row.

Defaults the ADRs do not fix (assumptions, changeable in `ragshelf.toml`):

| Setting | Default | Basis |
| --- | --- | --- |
| `chunking.overlap_ratio` | 0.10 | ADR 0002 gives the range 0–15%, "tuned with the eval"; the field accepts only that range. |
| `chunking.min_section_tokens` | 100 | ADR 0002: "sections under ~100 tokens merge". |
| `llm.cloud.base_url` | `https://openrouter.ai/api/v1` | The endpoint the prototype client already calls. |
| `llm.cloud.timeout_seconds`, `max_retries` | 60, 3 | Not in an ADR. T004 uses them and may adjust. |
| `llm.local.base_url` | `http://127.0.0.1:8081/v1` | Host and port of the ADR 0001 `llama-server` command. |
| `llm.local.timeout_seconds`, `max_retries` | 120, 1 | Not in an ADR. T004 uses them and may adjust. |
| `llm.route` | `cloud` | ADR 0001 names the cloud route as the default. |

Not included: the `llama-server` launch arguments (context size, batch sizes). T013 owns starting the server and adds them.

Choices not fixed by the task:

- `RAGSHELF_*` overrides are read from the process environment only, not from `.env`, so `.env` holds nothing but secrets and the variables the prototype still reads.
- `load_secrets` accepts the key from the process environment as well as `.env`. "Secrets from `.env` only" is implemented as "never from `ragshelf.toml`".
- `apply_environment` overwrites existing values of the four variables: the configuration is the single source, and a relative `HF_HOME` from `.env` would otherwise depend on the working directory.

Checks (run by the main session):

| Criterion | Check | Outcome |
| --- | --- | --- |
| 1 | `test_defaults_carry_the_adr_values`, `test_the_tracked_toml_file_changes_no_default` | verified |
| 2 | `test_environment_overrides_toml`, `test_toml_overrides_a_default` | verified |
| 3 | `test_hash_is_stable_across_loads`; `test_hash_changes_when_any_setting_changes` (changes each of the leaf settings in turn and expects a new, distinct hash); `test_secrets_stay_out_of_the_hash_and_repr`; `test_secrets_cannot_be_set_in_toml` | verified |
| 4 | `test_paths_and_hash_ignore_the_working_directory`, `test_relative_overrides_resolve_from_the_repository_root`; also by hand: `load_settings()` from the repository root and from `%TEMP%` gave the same hash and the same absolute `paths.library` | verified |

Command: `venv/Scripts/python.exe -m pytest tests/test_config.py` → 16 passed. The full suite (`venv/Scripts/python.exe -m pytest`) → 25 passed. `pip check` reports no broken requirements; `pip freeze --all` matches `requirements.txt` except the editable `ragshelf` entry.

Limitations:

- No independent review by the implementation session: the task is below tier 3, deletes nothing, and writes no persisted data.
- No module uses the configuration yet (out of scope); the hash format is first consumed by T008's index manifest.
- The default paths were not checked for existence; `data/cache`, `data/traces`, and `data/eval` do not exist yet and are created by the tasks that write to them.
