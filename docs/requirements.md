# Requirements

Confirmed product requirements for ragshelf. Each entry records where it was confirmed. Technical choices that implement them live in [docs/decisions/](decisions/); planned work lives in [ROADMAP.md](../ROADMAP.md).

## Confirmed

| ID | Requirement | Confirmed |
| --- | --- | --- |
| R1 | ragshelf is a retrieval-augmented generation system over a personal library of PDF and other text documents. | User, 2026-11-14 (constraints in [ADR 0001](decisions/0001-model-stack.md)) |
| R2 | Documents and queries may be in several languages; Russian and Slovak queries over mostly English documents must work. | User, 2026-11-14 (ADR 0001) |
| R3 | The primary use case is question answering over the whole library with citations to the source document and its location (page or section). When the library holds no supporting evidence, the system says so instead of answering. | User, 2026-11-15 |
| R4 | Drafting academic paragraphs on a topic is a secondary mode built on the same retrieval pipeline. | User, 2026-11-15 |
| R5 | The core is a Python library with a command-line interface for ingestion, querying, and evaluation. The Streamlit app is a thin interface over the same library. | User, 2026-11-15 |
| R6 | Document metadata (title, authors, year, DOI where present) is extracted automatically. A `metadata.json` supplied with a document overrides the extracted values. | User, 2026-11-15 |
| R7 | The prototype pipeline is replaced module by module with the stack in ADR 0001. Replaced prototype code and `legacy/` are deleted; Git keeps the history. | User, 2026-11-15 |
| R8 | One model in GPU memory at a time; everything is installed inside the project; a cloud generation model is the default and a local model works offline. | User, 2026-11-14 (ADR 0001) |

## Not decided

Open questions are tracked in [STATUS.md](../STATUS.md) ("Open decisions") until they are resolved here or in an ADR.
