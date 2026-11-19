# ragshelf

Retrieval-augmented generation (RAG) over a personal library of text documents.

The project began as an unfinished prototype of a knowledge base of scientific articles. It is being turned into a general RAG project for PDF and other text documents. The new parse-only ingestion stage scans originals and caches local MinerU output. Indexing, retrieval, and the interface still contain prototype code and are replaced by later roadmap tasks.

## Layout

| Path | Contents |
| --- | --- |
| `src/ragshelf/` | The Python package. |
| `src/ragshelf/parse/` | Document scan, content hashes, local MinerU adapter, and checksummed parse cache. |
| `src/ragshelf/loaders/` | Text extraction from documents (`universal_loader`: PDF). |
| `src/ragshelf/processing/` | Cleaning and chunking. |
| `src/ragshelf/embeddings/` | Embedding models (BGE, SciBERT, their weighted combination). |
| `src/ragshelf/store/` | Vector index over processed documents (FAISS). |
| `src/ragshelf/retrieval/` | Reranking of search results. |
| `src/ragshelf/llm/` | Chat clients behind one interface: the DeepSeek platform (default cloud provider), OpenRouter (alternative cloud provider), and llama-server (local). |
| `src/ragshelf/generation/` | Answer generation from retrieved chunks. |
| `src/ragshelf/app/` | Streamlit user interface. |
| `src/ragshelf/cli.py` | The `ragshelf` command-line interface; see [Commands](#commands). |
| `src/ragshelf/config.py`, `ragshelf.toml` | Typed configuration and its file; see [Configuration](#configuration). |
| `tests/` | pytest tests. |
| `docs/engineering/` | Development process and AI-assistant policies. |
| `data/` | Local documents and derived data; not published. See [data layout](docs/data-layout.md). |
| `models/` | Locally downloaded model weights and caches (MinerU, Hugging Face, GGUF, NLTK data); not published. |
| `.tools/` | Project-local third-party binaries (llama.cpp `llama-server`); not published. |
| `docs/decisions/` | Technical decisions (ADRs): the [model stack](docs/decisions/0001-model-stack.md), the [pipeline architecture](docs/decisions/0002-pipeline-architecture.md), and the [DeepSeek platform as the cloud route](docs/decisions/0003-deepseek-platform-cloud-route.md) (all accepted). |
| `docs/research/` | Research notes and reports behind the decisions. |
| `docs/requirements.md` | Confirmed product requirements. |
| `ROADMAP.md`, `tasks/` | Planned milestones and task files ([format](docs/engineering/TASK_FORMAT.md)). |

Code reads data paths relative to the repository root, so run it from there. `ragshelf ingest --parse-only` runs the scan/cache stage. Full index ingestion is planned for [T009](tasks/T009-ingest-command.md). The migrated library no longer supplies the old `article_<N>/` inputs expected by the prototype store; use the parse-only path while its replacement is developed.

## Commands

Run everything with the project's interpreter in `venv/`, from the repository root (PowerShell):

```powershell
venv\Scripts\ragshelf.exe --help        # the console script
venv\Scripts\python.exe -m ragshelf --help   # the same through the module
```

The CLI has five subcommands: `ingest`, `search`, `ask`, `eval`, and `inspect`. `inspect` works over the parse cache without loading any model: `ragshelf inspect <doc_id>` prints a document's metadata (with the source of each value) and its heading outline, and `ragshelf inspect --all` prints one full record per library document. It needs the cache from the stage below. The parse-only ingestion stage is available:

```powershell
venv\Scripts\ragshelf.exe ingest --parse-only
```

It scans `paths.library` (default `data/library/`) recursively and writes to `paths.cache/parse` (default `data/cache/parse/`). Each supported original receives a path-based `doc_id` and SHA-256. Sidecar JSON, unsupported files, Office lock files, symbolic links, and junctions are skipped. Supported formats follow the installed MinerU registry; UTF-8 `.md` and `.txt` pass through without MinerU and use logical page index 0.

Parsing runs locally in process. PDF/image inputs use MinerU's `standard` tier; Office, HTML, and EPUB use the installed kit's native `flash` dispatch. The adapter disables remote VLM use and rejects enabled LLM-aided remote features. HTML identity includes its source location and the local resources actually consumed by the native converter. Cache identity includes the source bytes, format, parser/runtime versions, and parser/render settings; changing embedding or retrieval settings does not invalidate parsing.

The command prints per-document cache hit, parsed, or failed status and a total. Exit 0 means no failures; exit 1 means a batch or document failure. A valid cache hit verifies bundle checksums and does not load the MinerU model runtime. A miss parses a source snapshot, validates output and unchanged inputs, and publishes the completed bundle; runtime ownership and GPU cache are released after a parsing batch. See [data layout](docs/data-layout.md) for artifacts and [T005](tasks/T005-document-scan-and-parse-cache.md) for verification and current limitations.

Bare `ingest`, `search`, `ask`, and `eval` remain placeholders: they print "not implemented yet" and exit with code 2 until their tasks in [ROADMAP.md](ROADMAP.md) are implemented.

Tests use pytest, installed by the `dev` extra (`pip install -e ".[dev]"`; already pinned in `requirements.txt`):

```powershell
venv\Scripts\python.exe -m pytest           # fast tests; tests marked `slow` are deselected
venv\Scripts\python.exe -m pytest -m slow   # tests that load real models
```

## Configuration

`src/ragshelf/config.py` defines every setting with its default: data and model paths, model IDs, chunking and retrieval parameters, and the cloud and local LLM routes. The defaults are the values decided in the ADRs. A value is taken from the first place that sets it:

1. an environment variable `RAGSHELF_<SECTION>__<KEY>`, for example `RAGSHELF_RETRIEVAL__RRF_K=30`;
2. [ragshelf.toml](ragshelf.toml) at the repository root, which lists every key commented out;
3. the default.

Unknown keys are errors. Relative paths are taken from the repository root, whatever the working directory is. `config_hash()` returns a SHA-256 of all settings and identifies a pipeline setup.

The LLM route is `llm.route` (`cloud` or `local`); the cloud route uses the provider named by `llm.cloud_provider`: `deepseek` (default, [ADR 0003](docs/decisions/0003-deepseek-platform-cloud-route.md)) or `openrouter`.

Secrets are not settings: `load_secrets()` reads `DEEPSEEK_API_KEY` and `OPENROUTER_API_KEY` from the process environment or `.env`, and they are not part of the hash. Only the key of the provider in use is needed. The remaining prototype modules are switched over as their replacement tasks are implemented.

## Dependencies

Everything runs from inside the project: the interpreter (Python 3.14.10) lives in `.python/`, and `venv/` is created from it, so nothing is installed system-wide. Neither folder is published.

`pyproject.toml` lists the direct dependencies; `requirements.txt` pins the exact versions installed in `venv/` (torch built for CUDA 13.0), with `ragshelf` itself installed in editable mode. Python 3.15 is not used yet because `faiss-cpu` publishes no Windows wheels for it.

The selected models and tools are recorded in [docs/decisions/0001-model-stack.md](docs/decisions/0001-model-stack.md) together with measurements on the development PC. They are installed and downloaded locally, but the code still uses the prototype's models (except the cloud generation model) until the pipeline is reworked.

Secrets go in `.env`; copy `.env.example`.

## License

MIT, see [LICENSE](LICENSE). Third-party dependencies, models, and the bundled skills under `.agents/skills/` keep their own licenses.
