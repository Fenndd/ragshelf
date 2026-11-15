---
id: T002
title: Add the CLI entry point and test harness
milestone: M1
status: planned
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

Not started.
