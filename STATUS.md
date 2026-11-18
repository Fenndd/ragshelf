# Status

Updated: 2026-11-18

## Phase

Implementation started. Active milestone: M2 — Persistent incremental index ([ROADMAP.md](ROADMAP.md)). T001–T003 are `done`, accepted and committed locally. [T004](tasks/T004-llm-clients.md) is `done`: the user accepted it on 2026-11-17 and instructed continuation with T005. M1 exit criteria are met. T004 rework resolved T004-REV-01, T004-REV-02, and T004-FOLLOWUP-01; its dated evidence includes **96 passing full-suite tests**, **65 passing LLM tests**, and an independent startup review with no supported findings. See [T004 acceptance](tasks/T004-llm-clients.md#acceptance--2026-11-17), [resolution evidence](tasks/T004-llm-clients.md#rework-result--2026-11-17), and the preserved [original review](docs/reviews/T004-2026-11-16.md).

[T005](tasks/T005-document-scan-and-parse-cache.md) is `review`: the scan/cache and `ingest --parse-only` implementation is present. The installed-runtime synthetic PDF/HTML smoke parsed both files and then returned two cache hits; the final fast suite passed **124 tests** with one slow test deselected. The final independent review found no remaining supported findings and passed 38 focused tests; the real 21-PDF / 1,297-page library parse completed with **21 parsed, 0 failed** in **917.8 s**, followed by **21 hits, 0 parsed, 0 failed** in **1.5 s**. The cache-hit guard verified that no parser/model runtime was imported. The user-approved file migration preserved 21 unique PDFs and 21 metadata sidecars with hash verification. On 2026-11-18 the user reported manually deleting the 35 empty legacy directories. Verification confirmed their absence, all 42 retained file hashes against migration evidence, and 21 cache hits with no parsing or model-runtime imports. All five acceptance criteria are verified; the previous cleanup blocker is resolved. User acceptance is pending. See T005 for evidence.

The local T004 commit removes `data/README.md` from the protected data tree and adds [docs/data-layout.md](docs/data-layout.md). That documentation relocation moved no library data or model files. The subsequent T005 migration is described separately above. The commit has not been pushed.

## Done

- Repository layout (`src/ragshelf/`, `data/`, `models/`), see [README.md](README.md) and [data layout](docs/data-layout.md).
- Shared AI-assistant infrastructure for Claude Code and Codex: [AGENTS.md](AGENTS.md), `.agents/skills/`, `.claude/`, [docs/engineering/](docs/engineering/).
- Project-local environment: Python 3.14.10 in `.python/`, `venv/` from [requirements.txt](requirements.txt), llama.cpp in `.tools/`.
- Model stack selected, downloaded, and smoke-tested on the development PC: [docs/decisions/0001-model-stack.md](docs/decisions/0001-model-stack.md).
- Cloud generation: DeepSeek platform, model `deepseek-flash` (`llm.deepseek` in `src/ragshelf/config.py`, ADR 0003, added in T004); OpenRouter `deepseek/deepseek-v4.1-flash-1017` kept as `llm.openrouter`.
- Confirmed requirements: [docs/requirements.md](docs/requirements.md) (Q&A with citations as the primary use case, CLI + thin Streamlit, automatic metadata with sidecar override, prototype replaced and deleted).
- Research on production RAG architecture: [docs/research/reports/Production RAG architecture.md](docs/research/reports/Production%20RAG%20architecture.md).
- Pipeline architecture with a module-by-module review of the prototype, accepted 2026-11-16: [ADR 0002](docs/decisions/0002-pipeline-architecture.md).
- Roadmap and task files: [ROADMAP.md](ROADMAP.md), `tasks/T001`–`T021`.
- T001: dead prototype code and `hdbscan` removed.
- T002: `ragshelf` console script with placeholder subcommands `ingest`, `search`, `ask`, `eval`; pytest harness with the `slow` marker.
- T003: typed configuration in `src/ragshelf/config.py` and `ragshelf.toml`, with a configuration hash and separate secrets.
- T004: cloud and local LLM clients, provider selection, and application-startup environment initialization; accepted 2026-11-17.

## Not verified

- The OpenRouter client has unit tests but has not been run against its real endpoint.
- The full pipeline with the new models, the query-translation step, and retrieval quality on Russian/Slovak → English queries.
- `lancedb` installation on Python 3.14 (abi3 Windows wheels exist on PyPI; not installed yet).
- Document processing and generation through the remaining prototype code (only imports are checked; the Streamlit app's initial render was checked before T001). The parse-only entry point now exists; full index ingestion remains T009. The migrated library no longer contains the prototype store's old document inputs.
- Whether Python 3.15 is still blocked: `hdbscan` is removed, `faiss-cpu` remains until T009.

## Open decisions

| Decision | Options | Notes |
| --- | --- | --- |
| Who writes the gold-set queries | The user, or the assistant drafts from the documents and the user corrects | Needed in T010. |
| Reference-list extraction with GROBID | Install Docker Desktop with WSL2 and run GROBID, or keep parsing the reference block that MinerU extracts with the LLM | GROBID has no native Windows support; WSL2 needs administrator rights, a reboot, and a system-wide install outside the project. Until decided, use the MinerU + LLM path. See the ADR's Consequences. |

## Pending setup

No T004 credentials or setup are pending.

## Next step

1. User review and acceptance of T005; implementation and all acceptance checks are complete.
2. T006 depends on T005 being accepted (`done`); it has not started. No further broad check cycle is pending.
3. T005 and the project AI-infrastructure policy updates are committed locally; no push was requested or performed.
