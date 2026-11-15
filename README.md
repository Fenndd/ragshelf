# ragshelf

Retrieval-augmented generation (RAG) over a personal library of text documents.

The project began as an unfinished prototype of a knowledge base of scientific articles. It is being turned into a general RAG project for PDF and other text documents. Today only PDF extraction exists; the code is the original prototype moved into the layout below, minus the experiments and clustering modules that were on no working path.

## Layout

| Path | Contents |
| --- | --- |
| `src/ragshelf/` | The Python package. |
| `src/ragshelf/loaders/` | Text extraction from documents (`universal_loader`: PDF). |
| `src/ragshelf/processing/` | Cleaning and chunking. |
| `src/ragshelf/embeddings/` | Embedding models (BGE, SciBERT, their weighted combination). |
| `src/ragshelf/store/` | Vector index over processed documents (FAISS). |
| `src/ragshelf/retrieval/` | Reranking of search results. |
| `src/ragshelf/llm/` | LLM API client. |
| `src/ragshelf/generation/` | Answer generation from retrieved chunks. |
| `src/ragshelf/app/` | Streamlit user interface. |
| `docs/engineering/` | Development process and AI-assistant policies. |
| `data/` | Local documents and derived data; not published. See [data/README.md](data/README.md). |
| `models/` | Locally downloaded model weights and caches (MinerU, Hugging Face, GGUF, NLTK data); not published. |
| `.tools/` | Project-local third-party binaries (llama.cpp `llama-server`); not published. |
| `docs/decisions/` | Technical decisions (ADRs): the [model stack](docs/decisions/0001-model-stack.md) (accepted) and the [pipeline architecture](docs/decisions/0002-pipeline-architecture.md) (accepted). |
| `docs/research/` | Research notes and reports behind the decisions. |
| `docs/requirements.md` | Confirmed product requirements. |
| `ROADMAP.md`, `tasks/` | Planned milestones and task files ([format](docs/engineering/TASK_FORMAT.md)). |

Code reads data paths relative to the repository root, so run it from there. There is no ingestion entry point at the moment: the prototype's script was removed, and `ragshelf ingest` is planned in [T009](tasks/T009-ingest-command.md).

## Dependencies

Everything runs from inside the project: the interpreter (Python 3.14.10) lives in `.python/`, and `venv/` is created from it, so nothing is installed system-wide. Neither folder is published.

`pyproject.toml` lists the direct dependencies; `requirements.txt` pins the exact versions installed in `venv/` (torch built for CUDA 13.0), with `ragshelf` itself installed in editable mode. Python 3.15 is not used yet because `faiss-cpu` publishes no Windows wheels for it.

The selected models and tools are recorded in [docs/decisions/0001-model-stack.md](docs/decisions/0001-model-stack.md) together with measurements on the development PC. They are installed and downloaded locally, but the code still uses the prototype's models (except the cloud generation model) until the pipeline is reworked.

Secrets go in `.env`; copy `.env.example`.

## License

MIT, see [LICENSE](LICENSE). Third-party dependencies, models, and the bundled skills under `.agents/skills/` keep their own licenses.
