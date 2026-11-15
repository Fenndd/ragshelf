# Status

Updated: 2026-11-15

## Phase

Foundation complete. The repository, environment, and selected model stack are in place; the RAG pipeline itself still runs on the prototype's models and has not been reworked.

## Done

- Repository layout (`src/ragshelf/`, `scripts/`, `legacy/`, `data/`, `models/`), see [README.md](README.md).
- Shared AI-assistant infrastructure for Claude Code and Codex: [AGENTS.md](AGENTS.md), `.agents/skills/`, `.claude/`, [docs/engineering/](docs/engineering/).
- Project-local environment: Python 3.14.10 in `.python/`, `venv/` from [requirements.txt](requirements.txt), llama.cpp in `.tools/`.
- Model stack selected, downloaded, and smoke-tested on the development PC: [docs/decisions/0001-model-stack.md](docs/decisions/0001-model-stack.md).
- Cloud generation model switched to `deepseek/deepseek-v4.1-flash-1017` in `src/ragshelf/llm/deepseek_llm.py`.

## Not verified

- The cloud model: no request has been sent yet (no API key configured).
- The full pipeline with the new models, the query-translation step, and retrieval quality on Russian/Slovak → English queries.
- Document processing and generation through the current code after the move to the package layout (imports and the Streamlit app's initial render were checked).

## Open decisions

| Decision | Options | Notes |
| --- | --- | --- |
| Reference-list extraction with GROBID | Install Docker Desktop with WSL2 and run GROBID, or keep parsing the reference block that MinerU extracts with the LLM | GROBID has no native Windows support; WSL2 needs administrator rights, a reboot, and a system-wide install outside the project. Until decided, use the MinerU + LLM path. See the ADR's Consequences. |

## Pending setup

- Add the OpenRouter API key to `.env` as `DEEPSEEK_API_KEY`, then send a first request to confirm the cloud model.

## Next step

Rework the pipeline onto the selected stack: MinerU parsing, query translation to English, harrier embeddings with BM25, Qwen3-Reranker, and the cloud/local generators. Then build a small labelled query set to evaluate retrieval and answers.
