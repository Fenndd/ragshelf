---
id: T002
title: Add the CLI entry point and test harness
milestone: M1
status: done
depends_on: [T001]
area:
  - "src/ragshelf/cli.py"
  - "src/ragshelf/__main__.py"
  - "tests/**"
  - "pyproject.toml"
  - "requirements.txt"
  - "README.md"
---

# T002 — Add the CLI entry point and test harness

## Goal

Provide a `ragshelf` command with the planned subcommands and a pytest setup that later tasks extend.

## Sources

- [Requirement R5](../docs/requirements.md)
- [Layering in ADR 0002](../docs/decisions/0002-pipeline-architecture.md)

## Scope

In scope: Console script `ragshelf` (argparse, standard library) with subcommands `ingest`, `search`, `ask`, `eval`; each prints "not implemented yet" and exits with code 2. `python -m ragshelf` does the same. `pytest` as a `dev` optional dependency; `tests/` with a `slow` marker for tests that load real models, deselected by default; a test for the CLI. README section "Commands".

Out of scope: Any subcommand behavior. Fakes for models (added with the interfaces they imitate).

## Acceptance Criteria

1. `ragshelf --help` lists the four subcommands.
2. `ragshelf search x` exits with code 2 and prints "not implemented yet".
3. `pytest` runs the CLI test and passes; `pytest -m slow` selects no tests yet.
4. README documents how to run the CLI and the tests.

## Checks

- `venv/Scripts/ragshelf.exe --help`
- `venv/Scripts/ragshelf.exe search x; echo $LASTEXITCODE` (PowerShell) prints 2.
- `venv/Scripts/python.exe -m pytest` and `venv/Scripts/python.exe -m pytest -m slow`.

## Open Questions

None

## Result

Accepted by the user 2026-11-16 after the independent review below and the fix for its one minor finding (T002-R1). Committed as one commit after acceptance. Done in the main session; nothing was delegated.

What was done:

- `src/ragshelf/cli.py`: argparse parser `ragshelf` with subcommands `ingest`, `search`, `ask`, `eval`. Each takes positional arguments and whatever follows the first one as a placeholder (`argparse.REMAINDER`), prints `ragshelf <command>: not implemented yet` to stderr, and returns exit code 2. An unknown option before the first positional, such as `ragshelf search --example`, is an argparse usage error (also exit code 2) and does not reach the placeholder handler. `main(argv)` returns the exit code, so tests call it in-process. The module imports only the standard library.
- `src/ragshelf/__main__.py`: `python -m ragshelf` calls the same `main`.
- `pyproject.toml`: console script `ragshelf = "ragshelf.cli:main"`; optional dependency group `dev` with `pytest`; pytest configuration (`testpaths = ["tests"]`, the `slow` marker, `-m "not slow"` by default, `--strict-markers`, `--import-mode=importlib`).
- `tests/test_cli.py`: 9 test cases covering the help text, every subcommand, `search x`, a missing and an unknown subcommand, and `python -m ragshelf` in a subprocess.
- `venv/`: installed `pytest 9.2.0` with `iniconfig 2.3.1` and `pluggy 1.7.0`; refreshed the editable install so `venv/Scripts/ragshelf.exe` exists. `requirements.txt` has the three new pins.
- `README.md`: section "Commands" (CLI and tests); layout rows for `cli.py` and `tests/`.

Choices not fixed by the task:

- The message goes to stderr, because it reports that the command did nothing.
- `--import-mode=importlib` (pytest's recommendation for new projects) lets test files in different folders share a basename without `__init__.py` files. Shared helpers such as `tests/fakes.py` will need a `pythonpath` entry or a `conftest.py` fixture when T004 adds them.
- `tests/` has no `conftest.py` yet: nothing needs one.

Checks (run by the main session):

| Criterion | Check | Outcome |
| --- | --- | --- |
| 1 | `venv/Scripts/ragshelf.exe --help` lists `ingest`, `search`, `ask`, `eval`; exit code 0 | verified |
| 2 | `venv/Scripts/ragshelf.exe search x` prints `ragshelf search: not implemented yet`; `$LASTEXITCODE` is 2. `venv/Scripts/python.exe -m ragshelf ask` behaves the same | verified |
| 3 | `venv/Scripts/python.exe -m pytest`: 9 passed. `venv/Scripts/python.exe -m pytest -m slow`: 9 deselected, 0 selected (pytest exit code 5, "no tests collected") | verified |
| 4 | Read the README diff | verified |

Also checked: `pip check` reports no broken requirements; `pip freeze --all` matches `requirements.txt` except the editable `ragshelf` entry.

Limitations:

- At implementation handoff, no independent review had been performed. The subsequent independent review is recorded below.
- `pytest -m slow` exits with code 5 until a slow test exists. A script that treats any non-zero code as failure must allow for that.

### Independent review — 2026-11-16

Verdict: **accept after minor fixes**. All four acceptance criteria are met; one minor documentation inconsistency remains open. No blocker or major finding was identified. This verdict is advisory, not user acceptance; the task remains in `review`.

Reviewed by Codex independently of the implementation, without subagents. Review target: the working-tree changes relative to `0b77455`, including untracked `src/ragshelf/cli.py`, `src/ragshelf/__main__.py`, and `tests/test_cli.py`. `git log --oneline --grep 'T002'` found no task commit. Sources checked: this task, requirements R5, ADR 0001, ADR 0002, the ROADMAP entry, and the workflow's Checks and Review rules. Implementation Result claims were independently checked rather than treated as evidence.

The review itself was read-only. This record was subsequently added at the user's request; it does not implement the proposed fix.

#### Acceptance criteria

| Criterion | Verdict | Evidence |
| --- | --- | --- |
| 1. Help lists all four subcommands | met | `venv/Scripts/ragshelf.exe --help`: `ingest`, `search`, `ask`, `eval`; exit 0. |
| 2. `search x` reports the placeholder and exits 2 | met | `venv/Scripts/ragshelf.exe search x`: stderr `ragshelf search: not implemented yet`; exit 2. |
| 3. CLI tests pass; no slow tests are selected yet | met | `venv/Scripts/python.exe -m pytest`: 9 passed, exit 0. With `-m slow`: 9 deselected, 0 selected, exit 5 (expected for an empty selection). |
| 4. README documents CLI and test commands | met | `README.md:33-48` documents both entry points, placeholder behavior, and default/slow pytest commands; the commands were independently checked. |

#### Open finding

**T002-R1 — minor: the Result overstates argument acceptance.**

- Location at review: `tasks/T002-cli-and-test-harness.md:56` and `src/ragshelf/cli.py:37-38`.
- Evidence: the Result says "Each accepts any arguments for now", and the parser comment says "accept anything". However, `venv/Scripts/ragshelf.exe search --example` prints `ragshelf: error: unrecognized arguments: --example` and exits 2 without reaching the placeholder handler. `venv/Scripts/ragshelf.exe search x --example` prints `ragshelf search: not implemented yet` and exits 2. `argparse.REMAINDER` does not accept an unknown option before the first positional argument in this parser.
- Consequence: documentation promises behavior the CLI does not provide; checking only exit code 2 would hide the difference.
- Proposed fix: narrow the Result and parser comment to describe actual argument handling. Supporting arbitrary options is not required by this task, so expanding parser behavior is unnecessary for acceptance.
- Status: resolved 2026-11-16 by the implementation session with the proposed fix. The Result bullet for `cli.py` and the parser comment now describe the actual argument handling; parser behavior is unchanged. Rechecked after the fix: `ragshelf.exe search --example` → `unrecognized arguments`, exit 2; `ragshelf.exe search x --example` → `not implemented yet`, exit 2; `pytest` → 9 passed.

#### Independently executed checks

Python checks used `PYTHONDONTWRITEBYTECODE=1`; pytest used `PYTEST_ADDOPTS='-p no:cacheprovider'` to avoid writing bytecode or pytest cache into the repository. No dependencies were installed.

| Check | Result |
| --- | --- |
| Required help, `search x`, default pytest, and `pytest -m slow` commands | verified; outputs and exit codes are recorded in the criteria table above. |
| Both executable and module entry points with `--help`, `ingest`, `search x`, `ask`, `eval`, no subcommand, and an unknown subcommand | verified; all 14 invocations returned expected exit codes, and each placeholder invocation printed the required message. |
| Import `ragshelf.cli` in a separate Python process and inspect newly imported modules | verified; no non-standard-library modules other than `ragshelf` were imported. |
| Two synthetic marker tests in a temporary directory outside the repository, using the project's pytest configuration | verified; default selection: 1 passed, 1 deselected. `--collect-only -m slow`: only the slow test selected, without execution. |
| `venv/Scripts/python.exe -m pip check` | verified; `No broken requirements found.`, exit 0. |
| `venv/Scripts/python.exe -m pip freeze --all` compared with `requirements.txt` | verified; versions match after standard package-name normalization and exclusion of the editable `ragshelf` entry. |
| Installed distribution metadata | verified; `pytest; extra == "dev"` and console entry point `ragshelf.cli:main` are present. |
| `git diff --check` | verified; exit 0, with only CRLF-to-LF normalization warnings. |
| `git status --short` before and after review | verified; the changed/untracked path set was unchanged. |

#### Conformance, scope, and repository hygiene

- R5 and ADR 0002 layering: the CLI only parses and dispatches; no pipeline logic or model loading was added. Storage, identity, chunking, model settings, and GPU lifecycle are unchanged. No new ADR-level decision was identified.
- Source and dependency changes fit the declared area. The task, ROADMAP, and STATUS updates are required bookkeeping under the workflow. `pytest` is authorized by the task and ADR 0002; `iniconfig` and `pluggy` are its dependencies. No unrelated refactor was found.
- Tests check exit codes, output, and module execution. The required placeholder wording is part of the acceptance criteria. The real console executable was additionally exercised by the reviewer.
- ROADMAP and STATUS consistently describe an uncommitted task in `review`. `data/README.md` needs no T002 update because document processing is unchanged. The other independently checkable Result claims were confirmed.
- `git ls-files` contains no local data, models, interpreter, tools, environment, or `.env` files, except the explicitly allowed `data/README.md`. Pattern scans of tracked files and new T002 files found no typical API keys, private keys, credential literals, personal paths, or email addresses. Commit-message email matches were service `Co-Authored-By` addresses, not personal addresses. No MinerU invocation was added; `--remote` appears in the checked ADR as a prohibition, not an execution path.

#### Not verified and remaining action

- Historical execution by the implementer cannot be proved from the Result text; the reported check outcomes were independently reproduced during this review.
- Clean-environment installation was not tested because installations were outside the read-only authorization; the existing `venv` was checked.
- Real models and GPU behavior were not tested because T002 does not touch models. No real slow tests exist or were executed; the synthetic slow probe was collected only. A GPU availability check was therefore unnecessary.
- Secret scanning covered current tracked/untracked files and commit messages, not every historical Git object, and is not proof that all possible confidential information is absent.

Remaining action: resolve T002-R1, then obtain user acceptance. No architecture or requirements decision is needed. Totals: 0 blocker, 0 major, 1 minor.

Follow-up, 2026-11-16: T002-R1 is resolved (see its Status above) and the user accepted the task. The verdict text above is the reviewer's record from before the fix.
