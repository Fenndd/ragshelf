---
id: T021
title: Remove leftovers and update documentation
milestone: M5
status: planned
depends_on: [T018, T020]
area:
  - "pyproject.toml"
  - "requirements.txt"
  - "README.md"
  - "data/README.md"
  - "STATUS.md"
  - "src/ragshelf/**"
---

# T021 — Remove leftovers and update documentation

## Goal

Leave no prototype code or unused dependency and make the documents describe the finished system.

## Sources

- [Requirement R7](../docs/requirements.md)

## Scope

In scope: Remove any remaining prototype module or unused package; regenerate `requirements.txt`; recheck whether Python 3.15 is now possible (record the result, do not upgrade); update README layout and commands, data/README, STATUS.

Out of scope: Upgrading Python.

## Acceptance Criteria

1. Every package in `pyproject.toml` is imported somewhere in `src/` (or is a documented runtime tool such as `mineru`).
2. No module under `src/` is unreferenced by the CLI, the app, or tests.
3. README and data/README match the tree.

## Checks

- `git grep` per dependency name.
- `venv/Scripts/python.exe -m pytest` and `-m slow`.
- Diff review.

## Open Questions

None

## Result

Not started.
