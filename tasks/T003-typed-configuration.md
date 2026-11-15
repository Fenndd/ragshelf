---
id: T003
title: Add typed configuration
milestone: M1
status: planned
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

Not started.
