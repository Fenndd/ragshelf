# Status

Updated: 2026-11-16

## Phase

Implementation started. Active milestone: M1 — Clean base ([ROADMAP.md](ROADMAP.md)). [T001](tasks/T001-remove-dead-prototype-code.md) is `done`: accepted after independent review and user-approved dependency-check clarifications on 2026-11-16, and committed (not pushed). [T002](tasks/T002-cli-and-test-harness.md) is `done`: independent review on 2026-11-16 found all four acceptance criteria met, its one minor finding (T002-R1) is fixed, the user accepted the task, and it is committed (not pushed). [T003](tasks/T003-typed-configuration.md) is `done`: accepted by the user on 2026-11-16 and committed (not pushed). T004 is next; M1 is not complete.

## Done

- Repository layout (`src/ragshelf/`, `data/`, `models/`), see [README.md](README.md).
- Shared AI-assistant infrastructure for Claude Code and Codex: [AGENTS.md](AGENTS.md), `.agents/skills/`, `.claude/`, [docs/engineering/](docs/engineering/).
- Project-local environment: Python 3.14.10 in `.python/`, `venv/` from [requirements.txt](requirements.txt), llama.cpp in `.tools/`.
- Model stack selected, downloaded, and smoke-tested on the development PC: [docs/decisions/0001-model-stack.md](docs/decisions/0001-model-stack.md).
- Cloud generation model switched to `deepseek/deepseek-v4.1-flash-1017` in `src/ragshelf/llm/deepseek_llm.py`.
- Confirmed requirements: [docs/requirements.md](docs/requirements.md) (Q&A with citations as the primary use case, CLI + thin Streamlit, automatic metadata with sidecar override, prototype replaced and deleted).
- Research on production RAG architecture: [docs/research/reports/Production RAG architecture.md](docs/research/reports/Production%20RAG%20architecture.md).
- Pipeline architecture with a module-by-module review of the prototype, accepted 2026-11-16: [ADR 0002](docs/decisions/0002-pipeline-architecture.md).
- Roadmap and task files: [ROADMAP.md](ROADMAP.md), `tasks/T001`–`T021`.
- T001: dead prototype code and `hdbscan` removed.
- T002: `ragshelf` console script with placeholder subcommands `ingest`, `search`, `ask`, `eval`; pytest harness with the `slow` marker.
- T003: typed configuration in `src/ragshelf/config.py` and `ragshelf.toml`, with a configuration hash and separate secrets.

## Not verified

- The cloud model: no request has been sent yet (no API key configured).
- The full pipeline with the new models, the query-translation step, and retrieval quality on Russian/Slovak → English queries.
- `lancedb` installation on Python 3.14 (abi3 Windows wheels exist on PyPI; not installed yet).
- Document processing and generation through the remaining prototype code (only imports are checked; the Streamlit app's initial render was checked before T001). There is no ingestion entry point until T009.
- Whether Python 3.15 is still blocked: `hdbscan` is removed, `faiss-cpu` remains until T009.

## Open decisions

| Decision | Options | Notes |
| --- | --- | --- |
| Migration of `data/inbox/` and `data/library/article_*` | Confirm moving originals to `data/library/` with sidecar metadata and deleting prototype outputs | Needed in T005. |
| Who writes the gold-set queries | The user, or the assistant drafts from the documents and the user corrects | Needed in T010. |
| Reference-list extraction with GROBID | Install Docker Desktop with WSL2 and run GROBID, or keep parsing the reference block that MinerU extracts with the LLM | GROBID has no native Windows support; WSL2 needs administrator rights, a reboot, and a system-wide install outside the project. Until decided, use the MinerU + LLM path. See the ADR's Consequences. |

## Pending setup

- Add the OpenRouter API key to `.env` (as `OPENROUTER_API_KEY` once T004 renames it; the prototype still reads `DEEPSEEK_API_KEY`). Needed in T004.

## Next step

Take up T004 (LLM clients): set it to `in_progress` in its task file and ROADMAP. Before its real cloud request, ask the user to put the key into `.env` as `OPENROUTER_API_KEY`; never print, log, or commit it. The mocked unit tests and the local `llama-server` request do not need the key. `llama-server` needs the GPU alone. Each task is committed after acceptance; push only when the user asks. T004 needs the OpenRouter key; T005 (M2) needs M1 accepted and the data-migration confirmation.
