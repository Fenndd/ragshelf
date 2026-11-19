---
id: T010
title: Build the gold evaluation set
milestone: M3
status: done
depends_on: [T005]
area:
  - "data/eval/**"
  - "docs/evaluation/gold-set-format.md"
  - "src/ragshelf/eval/__init__.py"
  - "src/ragshelf/eval/gold.py"
  - "tests/eval/test_gold.py"
---

# T010 — Build the gold evaluation set

## Goal

Create a labelled query set that measures retrieval and answers independently of chunking.

## Sources

- [Evaluation in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)
- [Research §4](../docs/research/reports/Production%20RAG%20architecture.md)
- [Requirements R2, R3](../docs/requirements.md)

## Scope

In scope: Document the format in `docs/evaluation/gold-set-format.md` (tracked). Write `data/eval/gold.jsonl` (untracked): at least 50 query intents, each in ru, sk, and en; relevant `doc_id`s with page or section spans; a short reference answer; 10–20% unanswerable intents. Include the query types the user actually asks (factual, comparison across documents, definition, method details).

Out of scope: Code for evaluation (T015, T018).

## Acceptance Criteria

1. `gold-set-format.md` defines every field.
2. `gold.jsonl` validates against the format (a check script or test), has ≥50 intents with all three languages, and 10–20% unanswerable.
3. Every referenced `doc_id` exists in `data/library/`.
4. The user has reviewed the set; the review is recorded in Result.

## Checks

- Validation script or test (written in this task; its path recorded in Result).
- Manual: user review.

## Open Questions

Resolved 2026-11-18 (user, in chat): a strong model writes the gold queries and the user reviews them (criterion 4). The user also permitted, for this task only, the writing agent to read the parsed text of the library documents (an exception to the Data Handling rule in AI_ORCHESTRATION.md; document text must not be copied into tracked files), and chose Opus 5.5 high (`opus-high`, tier 3) as the writer; both choices are the user's direct decision, not a routing-policy tier justification.

Planning change (2026-11-18): `area` gained `src/ragshelf/eval/__init__.py`, `src/ragshelf/eval/gold.py`, and `tests/eval/test_gold.py`, because criterion 2 requires a validation script or test and the original area had no tracked location for it. T015 and T018 own the rest of `src/ragshelf/eval/**` and depend on T010, so they run after it and extend the package.

## Result

### Current verification checkpoint — 2026-11-19

The user explicitly accepted the gold set and authorized merging its branch into `main` on 2026-11-19: “T010. Принимаю gold набор и разрешаю объединение его ветки с main.” T010 is `done` under that explicit user acceptance. Whether the user performed the separate review described in criterion 4 is not independently established; no per-intent review markings are inferred.

The local `main` branch was fast-forwarded from `5290e5c` to `4ab303e387a97758fd9fd42ce3fe6dfb3d40ba07`, incorporating `d7d8c0e` and `4ab303e` without a new merge commit. The four incoming tracked paths had no existing filesystem entries, including untracked or ignored collisions. SHA-256 snapshots of all 35 pre-existing modified/untracked files and the ignored gold artifacts matched immediately before and after the merge. No stash, reset, clean, push, branch deletion, or worktree deletion was performed; unrelated unfinished work was preserved.

Checks repeated in the merged main checkout with `PYTHONPATH` set to its `src`:

- `venv/Scripts/python.exe -m pytest tests/eval -q` — verified: **34 passed**.
- `venv/Scripts/python.exe -m ragshelf.eval.gold data/eval/gold.jsonl --library data/library --parse-cache data/cache/parse` — verified: exit 0, `OK`; 69 intents, all three languages for every intent, 11 unanswerable (15.9%), and 21 referenced documents; library identity and cached page-bound checks passed.
- `git diff --check` — verified: no whitespace errors (Git reported existing CRLF normalization warnings).

The full suite and a new semantic label review were not run for this merge. The implementation account below records the earlier evidence and its limitations.

### Implementation — 2026-11-19

Implemented on the branch `t010-gold-set` (worktree `.claude/worktrees/agent-a593cd14bd4d7f31d`), commits `d7d8c0e` and `4ab303e`; subsequently merged locally into `main` as recorded above, without pushing. The tracked files are `docs/evaluation/gold-set-format.md`, `src/ragshelf/eval/__init__.py`, `src/ragshelf/eval/gold.py`, and `tests/eval/test_gold.py`. The labelled set itself is untracked: `data/eval/gold.jsonl` and the review sheet `data/eval/gold-review.md`, both in the main checkout.

**Format conventions** (full definition in `gold-set-format.md`): one JSON object per line; `pages` are 1-based physical pages (content-list `page_idx` + 1); `doc_id` is the path relative to `data/library/` (the T005 scheme); unanswerable intents have empty evidence, `reference_answer` `NO_ANSWER`, and a required `unanswerable_reason`; `type` is factual, comparison, definition, or method.

**Validator** (`python -m ragshelf.eval.gold`): strict pydantic validation with line and field in every message (no record text is echoed); checks id uniqueness, all three languages, evidence iff answerable, minimum intents and the unanswerable share (both parameters), and with `--library` and `--parse-cache` that every `doc_id` exists and every page is within the parsed page count.

**Set statistics** (after the fixes below): 69 intents, ru/sk/en present for all; 11 unanswerable (15.9%); types factual 38, method 13, comparison 9, definition 9; all 21 library documents referenced; 11 multi-document and 29 multi-page intents. Up to 19 intents can be dropped in review while keeping the minimum of 50.

**Authoring and verification.** The set was written by an Opus 5.5 / high agent (Tier 3, chosen directly by the user; the user also permitted reading the parsed library text for this task). The author re-checked all 57 answerable intents against the cited cache pages by script. An independent read-only verifier (Tier 2, Sonnet 5.5 / high) then re-opened the cited pages of all 57 answerable intents and searched the whole cache for each of the 11 unanswerable ones. Verdict: no wrong labels (P1); all reference answers supported; all page numbers correct under the convention; all 11 unanswerable items confirmed unanswerable. It found seven weak intents (P2: incomplete evidence q022 and q052; ECR versus ECR-R q025; presupposing wording q048; merged constructs q055; mismatched compared outcomes q057; compound query q034) and about 14 minor items. All were addressed by a Tier 2 executor (q034 split into q034 and q069; q055 relabelled factual; q019 deliberately left unchanged because its abstract does not answer alone) and the format document gained two clarifying sentences (comparison also covers multi-document corroboration; compound questions are allowed but flagged in `notes`).

| Check | Result |
| --- | --- |
| `pytest tests/eval` (PYTHONPATH set to the worktree `src`) | verified: 34 passed (orchestrator re-run before the label fixes; the fix executor reported 34 passed after) |
| Validator over the real `gold.jsonl` with library and parse cache (criteria 2 and 3) | verified: exit 0, OK; 69 intents; every `doc_id` exists |
| Independent label verification | verified as described above; second pass after the fixes was not repeated |
| Full project suite | not run in this worktree (other tasks were in progress in the main checkout) |

**Known limitations.** The set is written by one labeller and skews toward abstracts and methods pages; document coverage is uneven (one review carries seven intents, the 706-page book only a few pages); many queries name the author or title, so document-level retrieval is easy and only page-level discrimination differentiates systems; about ten intents are close to the page wording (flagged in `notes`); about ten intents are two-part questions, so T015 must decide how to score both parts; Slovak and Russian quality was judged by models, not a native speaker.

**Acceptance.** Criteria 1–3 are verified. The user's explicit acceptance on 2026-11-19 and instruction to merge are recorded above. The review sheet remains available as an artifact; whether the user performed the separate review described in criterion 4 is not independently established, and acceptance does not assert that every entry was marked. T010 is `done` under the user's explicit acceptance; no new task is authorized by it.
