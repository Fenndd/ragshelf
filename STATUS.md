# Status

Updated: 2026-11-19

## Latest review-fix update — 2026-11-19

The four T006 findings in the [independent review](docs/reviews/T006-T011-2026-11-19.md) were fixed with regressions, and an independent reviewer checked the fixes. A further source-change race found during that review was fixed as well. The user chose sidecar-only document language; its implementation passed independent review and the fast suite passed **737 tests, 1 deselected**. After this change `inspect --all` returned 21 records, exit 0 and no stderr. The user reviewed the ten-document metadata sample and accepted T006 on 2026-11-19.

The accepted [language decision](docs/decisions/0002-pipeline-architecture.md#document-language-metadata--clarification-accepted-2026-11-19) is sidecar-only; `langdetect` remains a dependency solely for the legacy chunker pending T009. The user accepted T010 and authorized its local merge through `4ab303e`. The user authorized paid DeepSeek verification for T011 and accepted it. Twenty real-cloud translations passed the response-format checks; semantic review found 19 passes and one pass with a name-transliteration caveat. The API-reported token usage implies an estimated $0.00103155 at published off-peak prices; the actual deduction was not verified. T011 is `done`, with the local-model limitations recorded.

## Resume update — 2026-11-19

The T006 review-fix round is complete and the user accepted T006 and T011. The T010 branch was fast-forwarded into local `main`.

| Task | Status | State |
| --- | --- | --- |
| T005 | `done` | Accepted 2026-11-18. |
| T006 | `done` | Accepted after fixes, independent checks, sidecar-only language implementation and the user's ten-document metadata review. |
| T010 | `done` | The user accepted the gold set and authorized merging on 2026-11-19. Local `main` fast-forwarded to `4ab303e`; validator and 34 tests passed. Not pushed. |
| T011 | `done` | Accepted after its documented checks. DeepSeek: 20 format passes, 19 semantic passes and one caveat. The local-model check found two semantic failures. |

`README.md` now mentions `ragshelf inspect`. `pymupdf` and `langdetect` are still listed in `pyproject.toml`; removing them with the legacy code is T009's scope.

## Phase

Implementation started. Active milestone: M2 — Persistent incremental index ([ROADMAP.md](ROADMAP.md)). T001–T003 are `done`, accepted and committed locally. [T004](tasks/T004-llm-clients.md) is `done`: the user accepted it on 2026-11-17 and instructed continuation with T005. M1 exit criteria are met. T004 rework resolved T004-REV-01, T004-REV-02, and T004-FOLLOWUP-01; its dated evidence includes **96 passing full-suite tests**, **65 passing LLM tests**, and an independent startup review with no supported findings. See [T004 acceptance](tasks/T004-llm-clients.md#acceptance--2026-11-17), [resolution evidence](tasks/T004-llm-clients.md#rework-result--2026-11-17), and the preserved [original review](docs/reviews/T004-2026-11-16.md).

[T005](tasks/T005-document-scan-and-parse-cache.md) is `done`: the user accepted it on 2026-11-18 ([acceptance record](tasks/T005-document-scan-and-parse-cache.md#acceptance--2026-11-18)). [T006](tasks/T006-document-model-and-metadata.md) is `done` after user review and acceptance (see the table above). The T005 evidence follows: the scan/cache and `ingest --parse-only` implementation is present. The installed-runtime synthetic PDF/HTML smoke parsed both files and then returned two cache hits; the final fast suite passed **124 tests** with one slow test deselected. The final independent review found no remaining supported findings and passed 38 focused tests; the real 21-PDF / 1,297-page library parse completed with **21 parsed, 0 failed** in **917.8 s**, followed by **21 hits, 0 parsed, 0 failed** in **1.5 s**. The cache-hit guard verified that no parser/model runtime was imported. The user-approved file migration preserved 21 unique PDFs and 21 metadata sidecars with hash verification. On 2026-11-18 the user reported manually deleting the 35 empty legacy directories. Verification confirmed their absence, all 42 retained file hashes against migration evidence, and 21 cache hits with no parsing or model-runtime imports. All five acceptance criteria are verified; the previous cleanup blocker is resolved. See T005 for evidence.

[T011](tasks/T011-query-translation.md) (M3, query translation) is `done`, accepted after its documented checks. Scripted-client tests pass. A 20-query local check found two semantic failures and three caveats; the authorized DeepSeek check of the same 20 queries produced 19 semantic passes and one caveat, with all 20 responses passing the format check. This sample is not a full retrieval or answer-quality evaluation.

[T010](tasks/T010-gold-evaluation-set.md) (gold evaluation set) is `done`, accepted by the user on 2026-11-19 and merged locally via commits `d7d8c0e` and `4ab303e`. The labelled set is untracked in `data/eval/`: 69 intents in ru/sk/en, 11 unanswerable, all 21 documents referenced. Its validator and 34 tests passed after the merge. The merge was not pushed.

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
| Reference-list extraction with GROBID | Install Docker Desktop with WSL2 and run GROBID, or keep parsing the reference block that MinerU extracts with the LLM | GROBID has no native Windows support; WSL2 needs administrator rights, a reboot, and a system-wide install outside the project. Until decided, use the MinerU + LLM path. See the ADR's Consequences. |

## Pending setup

No T004 credentials or setup are pending.

## Next step

1. In a future development session, T007 follows accepted T006. T012 needs accepted T009 and T011, unless the user explicitly authorizes earlier continuation. Do not start new tasks in this session.
2. T005 and the project AI-infrastructure policy updates are committed locally; no push was requested or performed.
