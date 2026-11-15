---
id: T013
title: Add the reranker and the model lifecycle
milestone: M3
status: planned
depends_on: [T012]
area:
  - "src/ragshelf/retrieve/rerank.py"
  - "src/ragshelf/models/**"
  - "src/ragshelf/retrieval/**"
  - "src/ragshelf/cli.py"
  - "tests/retrieve/test_rerank.py"
  - "docs/decisions/0002-pipeline-architecture.md"
---

# T013 — Add the reranker and the model lifecycle

## Goal

Rerank fused candidates with Qwen3-Reranker and manage which model occupies the GPU, including the local LLM server.

## Sources

- [Reranker row and measurements in ADR 0001](../docs/decisions/0001-model-stack.md)
- [Models in GPU memory in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: Reranker over the top fused candidates, sigmoid scores, top-N to the caller. Lifecycle manager that ensures one model at a time, including starting and stopping `llama-server` for local mode. Measure the local query path (translate → embed → rerank → generate) with each swap strategy considered (restart server, CPU for embedder/reranker) and record the numbers and the chosen strategy in ADR 0002. Delete `retrieval/reranker.py`. A lexical fake reranker in `tests/fakes.py`.

Out of scope: Score thresholds for abstention (T017).

## Acceptance Criteria

1. Unit tests with the fake reranker check ordering and top-N.
2. A slow test ranks a relevant passage above two distractors.
3. Local-mode timings and peak VRAM per strategy are recorded in ADR 0002, and the chosen strategy keeps VRAM under 6 GiB without spilling to shared memory.
4. `retrieval/reranker.py` is deleted.

## Checks

- `venv/Scripts/python.exe -m pytest tests/retrieve/test_rerank.py` and `-m slow`
- Timing runs with `nvidia-smi` sampling, recorded in ADR 0002.

## Open Questions

None

## Result

Not started.
