---
id: T001
title: Remove dead prototype code
milestone: M1
status: ready
depends_on: []
area:
  - "legacy/**"
  - "scripts/chunk_experiment.py"
  - "scripts/process_sources.py"
  - "src/ragshelf/processing/cluster_hdbscan.py"
  - "src/ragshelf/processing/chunk_clusterization.py"
  - "src/ragshelf/processing/token_counter.py"
  - "pyproject.toml"
  - "requirements.txt"
  - "README.md"
  - "data/README.md"
---

# T001 — Remove dead prototype code

## Goal

Delete prototype code that is on no working path, so later tasks start from only the modules they replace.

## Sources

- [Requirement R7](../docs/requirements.md)
- [Prototype review in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: Delete `legacy/`, `scripts/chunk_experiment.py`, `scripts/process_sources.py` (it raises `TypeError` on `split_references` and imports clustering), `processing/cluster_hdbscan.py`, `processing/chunk_clusterization.py`, `processing/token_counter.py`. Remove `hdbscan` (and `scikit-learn` if no remaining module imports it) from `pyproject.toml`, uninstall them from `venv/`, refresh `requirements.txt`. Update README layout and data/README (no ingestion script until T009; `data/experiments/` keeps old outputs as reference).

Out of scope: Loader, chunker, embedders, store, reranker, LLM client, generation, and the Streamlit app (replaced in later tasks). Files under `data/`.

## Acceptance Criteria

1. The listed files and `legacy/` no longer exist.
2. No file under `src/` or `scripts/` references `cluster_hdbscan`, `chunk_clusterization`, `token_counter`, or `hdbscan`.
3. Every remaining module under `src/ragshelf/` except the Streamlit app imports without error.
4. `requirements.txt` matches `pip freeze` of `venv/` (excluding the editable `ragshelf` line format) and contains neither removed package.
5. README and data/README describe the tree as it is.

## Checks

- `git ls-files legacy scripts src/ragshelf/processing` shows only `src/ragshelf/processing/chunker.py` and `__init__.py`.
- `git grep -nE "cluster_hdbscan|chunk_clusterization|token_counter|hdbscan" -- src scripts pyproject.toml requirements.txt` prints nothing.
- `venv/Scripts/python.exe -c "import importlib,pkgutil,ragshelf; [importlib.import_module(m.name) for m in pkgutil.walk_packages(ragshelf.__path__,'ragshelf.') if 'app' not in m.name]"` exits 0.
- `venv/Scripts/python.exe -m pip freeze` compared with `requirements.txt`.
- Read the README and data/README diff.

## Open Questions

None

## Result

Not started.
