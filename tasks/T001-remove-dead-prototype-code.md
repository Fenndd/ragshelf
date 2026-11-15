---
id: T001
title: Remove dead prototype code
milestone: M1
status: done
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
4. `requirements.txt` matches `pip freeze --all` of `venv/`, excluding the editable `ragshelf` entry. `hdbscan` is absent from the environment and requirements; `scikit-learn` remains installed and pinned as a transitive dependency of `sentence-transformers`, but neither package is a direct dependency in `pyproject.toml`.
5. README and data/README describe the tree as it is.

User-approved clarification (2026-11-16): the original criterion 4 read "`requirements.txt` matches `pip freeze` of `venv/` (excluding the editable `ragshelf` line format) and contains neither removed package." The user confirmed retaining `scikit-learn` and using `pip freeze --all`. Installed `sentence-transformers` requires `scikit-learn>=1.1.0`, consistent with ADR 0002's conditional removal rule; `--all` includes the installed `pip` pin. This also clarifies the Scope's uninstall instruction: uninstall only `hdbscan`, and remove both packages from direct dependencies. The goal and dependent tasks are unchanged.

## Checks

- `git ls-files legacy scripts src/ragshelf/processing` shows only `src/ragshelf/processing/chunker.py` and `__init__.py`.
- `git grep -nE "cluster_hdbscan|chunk_clusterization|token_counter|hdbscan" -- src scripts pyproject.toml requirements.txt` prints nothing.
- `venv/Scripts/python.exe -c "import importlib,pkgutil,ragshelf; [importlib.import_module(m.name) for m in pkgutil.walk_packages(ragshelf.__path__,'ragshelf.') if 'app' not in m.name]"` exits 0.
- `venv/Scripts/python.exe -m pip freeze --all` compared with `requirements.txt`, excluding the editable `ragshelf` entry.
- Read the README and data/README diff.

## Open Questions

None

## Result

Accepted 2026-11-16 after independent review and the user-approved clarification of criterion 4. Final review verdict: accept. Committed as one commit after acceptance.

What was done:

- Deleted `legacy/` (9 files), `scripts/chunk_experiment.py`, `scripts/process_sources.py`, `src/ragshelf/processing/cluster_hdbscan.py`, `chunk_clusterization.py`, and `token_counter.py`. `scripts/` no longer exists because it is empty.
- `pyproject.toml`: removed `hdbscan` and `scikit-learn` from the direct dependencies (no remaining module imports either).
- `venv/`: uninstalled `hdbscan`; refreshed the editable install metadata with `pip install -e . --no-deps`.
- `requirements.txt`: removed the `hdbscan` pin and the comment pointing at `legacy/requirements-py311.txt`.
- `README.md`, `data/README.md`: describe the tree without the deleted paths; no ingestion entry point until T009; `data/experiments/chunking/` is kept as reference output.
- `.gitignore`: reworded one comment that named the deleted scripts as the writers of `reranked_*.json`, `faiss.index`, and `chunks.pkl`. The patterns are unchanged. This file is outside the `area` list; the change is a comment only.

Criterion 4 uses the user-approved clarification above. Independently inspected package metadata confirms `sentence-transformers 6.3.0` requires `scikit-learn>=1.1.0`; installed `scikit-learn` is 1.9.1. `hdbscan` is absent, and neither package remains in the installed `ragshelf` metadata's direct dependencies.

Checks independently rerun during review (2026-11-16):

| Criterion | Check | Outcome |
| --- | --- | --- |
| 1 | `git ls-files legacy scripts src/ragshelf/processing` lists only `__init__.py` and `chunker.py`; `legacy/` and `scripts/` are absent on disk | verified |
| 2 | `git grep -nE "cluster_hdbscan\|chunk_clusterization\|token_counter\|hdbscan" -- src scripts pyproject.toml requirements.txt` prints nothing | verified |
| 3 | The import walk over `ragshelf.*` without the app imports 16 modules and exits 0 (a `fitz` deprecation warning only); bytecode writes disabled | verified |
| 4 | `pip freeze --all` against `requirements.txt` with normalized package names and the editable entry excluded: no differences; `pip check` reports `No broken requirements found.` | verified under the user-approved clarification |
| 5 | Read the README and data/README diff against the tree | verified |

Independent review examined the full working-tree diff against `924d3df`, the requirements, both ADRs, the task, and its roadmap entry. The sole finding was the mismatch between the original criterion 4 and the reported verification. The user's clarification and the documentation corrections resolve it; no other confirmed findings remain. Additional checks: `git diff --check HEAD` passed; Git tracking and history checks found only the permitted `data/README.md` under protected paths; credential-pattern scanning found no confirmed leaks; `--remote` occurs only in documentary prohibitions. The reviewer made no implementation or environment changes; subsequent edits only record the user-approved clarification and acceptance.

The implementation session previously reported a separate subagent review using tier 2, preset `opus-medium` (Opus, medium effort), 86,015 worker tokens and 111 s. Those historical execution details are not independently verified by this review and are not evidence for acceptance.

Limitations:

- README still states that Python 3.15 is blocked by missing `faiss-cpu` Windows wheels. This was not rechecked against PyPI; ADR 0002 schedules the recheck for after `faiss-cpu` is removed (T009).
- Only imports were checked. The remaining prototype modules were not run.
- `venv/Scripts/python.exe -B -m pytest -p no:cacheprovider` failed with `No module named pytest`; the CLI executable is also absent. Both are planned in T002 and are not T001 criteria. No packages were installed; no slow tests or model inference were run.
