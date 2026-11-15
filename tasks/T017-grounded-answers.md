---
id: T017
title: Generate grounded answers with citations and abstention
milestone: M4
status: planned
depends_on: [T016, T014]
area:
  - "src/ragshelf/generate/**"
  - "src/ragshelf/prompts/**"
  - "src/ragshelf/cli.py"
  - "src/ragshelf/generation/**"
  - "src/ragshelf/trace.py"
  - "tests/generate/**"
---

# T017 — Generate grounded answers with citations and abstention

## Goal

Answer questions over the library in the query's language with verified citations, and abstain when evidence is missing.

## Sources

- [Requirement R3](../docs/requirements.md)
- [Retrieval and generation in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §1, §5](../docs/research/reports/Production%20RAG%20architecture.md)

## Scope

In scope: Versioned answer prompt (cite `[S<n>]`, use only the context, say when evidence is insufficient, answer in the original query's language, treat context as data). `ragshelf ask "<question>" [--local]`: search → rerank → context → generate; remove and report citations not in the context; abstain below the reranker-score threshold (set from gold-set data, value recorded) or when the model reports insufficient evidence. Output lists cited documents with pages. Trace gains prompt version, model, route, context IDs, answer, citations, abstention. Delete `generation/rag_chain.py`.

Out of scope: Drafting mode (T020). The UI (T019).

## Acceptance Criteria

1. Unit tests with the scripted client: valid citations kept, invented ones removed and reported, abstention below threshold, answer-language instruction set.
2. A test chunk containing an instruction ("ignore previous instructions…") does not change the output format in a scripted-client test and in one real cloud run.
3. `ragshelf ask` returns cited answers for 5 answerable and abstains for 3 unanswerable gold queries, cloud and local, recorded in Result.

## Checks

- `venv/Scripts/python.exe -m pytest tests/generate`
- `venv/Scripts/ragshelf.exe ask "..."` and `--local` runs.

## Open Questions

None

## Result

Not started.
