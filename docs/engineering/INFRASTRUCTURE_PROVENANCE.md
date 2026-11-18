# Infrastructure Provenance

- Preparation / transfer date: 2026-11-18
- Source: canonical AI Development Infrastructure source
- Source baseline: `5ab76bf2f5b726998b690b362a15c6e164f4ae85` (source working tree observed clean)
- Prior installed baseline: unavailable; no prior provenance receipt found
- State: applied; post-application static checks passed. Client loading and execution remain unverified.

## Installed or Merged Paths

| Source path | Destination path | Outcome |
| --- | --- | --- |
| `.agents/skills/model-routing/SKILL.md` | `.agents/skills/model-routing/SKILL.md` | Updated |
| `.agents/skills/security-best-practices/LICENSE.txt` | `.agents/skills/security-best-practices/LICENSE.txt` | Verified unchanged |
| `.agents/skills/security-best-practices/SKILL.md` | `.agents/skills/security-best-practices/SKILL.md` | Verified unchanged |
| `.agents/skills/security-best-practices/agents/openai.yaml` | `.agents/skills/security-best-practices/agents/openai.yaml` | Verified unchanged |
| `.agents/skills/security-best-practices/references/golang-general-backend-security.md` | `.agents/skills/security-best-practices/references/golang-general-backend-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/javascript-express-web-server-security.md` | `.agents/skills/security-best-practices/references/javascript-express-web-server-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/javascript-general-web-frontend-security.md` | `.agents/skills/security-best-practices/references/javascript-general-web-frontend-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/javascript-jquery-web-frontend-security.md` | `.agents/skills/security-best-practices/references/javascript-jquery-web-frontend-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/javascript-typescript-nextjs-web-server-security.md` | `.agents/skills/security-best-practices/references/javascript-typescript-nextjs-web-server-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/javascript-typescript-react-web-frontend-security.md` | `.agents/skills/security-best-practices/references/javascript-typescript-react-web-frontend-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/javascript-typescript-vue-web-frontend-security.md` | `.agents/skills/security-best-practices/references/javascript-typescript-vue-web-frontend-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/python-django-web-server-security.md` | `.agents/skills/security-best-practices/references/python-django-web-server-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/python-fastapi-web-server-security.md` | `.agents/skills/security-best-practices/references/python-fastapi-web-server-security.md` | Verified unchanged |
| `.agents/skills/security-best-practices/references/python-flask-web-server-security.md` | `.agents/skills/security-best-practices/references/python-flask-web-server-security.md` | Verified unchanged |
| `.agents/skills/security-threat-model/LICENSE.txt` | `.agents/skills/security-threat-model/LICENSE.txt` | Verified unchanged |
| `.agents/skills/security-threat-model/SKILL.md` | `.agents/skills/security-threat-model/SKILL.md` | Verified unchanged |
| `.agents/skills/security-threat-model/agents/openai.yaml` | `.agents/skills/security-threat-model/agents/openai.yaml` | Verified unchanged |
| `.agents/skills/security-threat-model/references/prompt-template.md` | `.agents/skills/security-threat-model/references/prompt-template.md` | Verified unchanged |
| `.agents/skills/security-threat-model/references/security-controls-and-assets.md` | `.agents/skills/security-threat-model/references/security-controls-and-assets.md` | Verified unchanged |
| `.agents/skills/session-teacher/SKILL.md` | `.agents/skills/session-teacher/SKILL.md` | Verified unchanged |
| `.agents/skills/session-teacher/references/original-gist.md` | `.agents/skills/session-teacher/references/original-gist.md` | Verified unchanged |
| `.claude/agents/opus-high.md` | `.claude/agents/opus-high.md` | Updated |
| `.claude/agents/opus-max.md` | `.claude/agents/opus-max.md` | Updated |
| `.claude/agents/opus-medium.md` | `.claude/agents/opus-medium.md` | Updated |
| `.claude/agents/sonnet-high.md` | `.claude/agents/sonnet-high.md` | Updated |
| `.claude/skills/model-routing/SKILL.md` | `.claude/skills/model-routing/SKILL.md` | Updated |
| `.claude/skills/security-best-practices/SKILL.md` | `.claude/skills/security-best-practices/SKILL.md` | Verified unchanged |
| `.claude/skills/security-threat-model/SKILL.md` | `.claude/skills/security-threat-model/SKILL.md` | Verified unchanged |
| `.claude/skills/session-teacher/SKILL.md` | `.claude/skills/session-teacher/SKILL.md` | Verified unchanged |
| `presets/codex-config.toml` | `.codex/config.toml` | Added |
| `.editorconfig` | `.editorconfig` | Verified unchanged |
| `.gitattributes` | `.gitattributes` | Verified unchanged |
| `.gitignore` | `.gitignore` | Verified unchanged |
| `templates/AGENTS.md` | `AGENTS.md` | Merged |
| `CLAUDE.md` | `CLAUDE.md` | Verified unchanged |
| `GEMINI.md` | `GEMINI.md` | Verified unchanged |
| `docs/engineering/AI_INFRASTRUCTURE_EVALUATION.md` | `docs/engineering/AI_INFRASTRUCTURE_EVALUATION.md` | Added |
| `docs/engineering/AI_ORCHESTRATION.md` | `docs/engineering/AI_ORCHESTRATION.md` | Updated |
| `docs/engineering/DEVELOPMENT_WORKFLOW.md` | `docs/engineering/DEVELOPMENT_WORKFLOW.md` | Updated |
| `docs/engineering/TASK_FORMAT.md` | `docs/engineering/TASK_FORMAT.md` | Updated |
| Generated transfer receipt | `docs/engineering/INFRASTRUCTURE_PROVENANCE.md` | New provenance record |

## Deliberate Adaptations and Omissions

- AGENTS.md preserves the existing project-specific context table: requirements, layout, ADR, roadmap/status and workflow pointers; shared execution, acceptance, delegation and safety rules updated.
- CLAUDE.md, GEMINI.md, .editorconfig and .gitattributes retained byte-for-byte; behavior already matches the shared template.
- .gitignore retained byte-for-byte; every generic source ignore is covered while Python, private documents/data, models, tools and runtime secret exclusions remain.
- Optional .codex/config.toml prepared with executor-only Sol/medium defaults: no existing project config or conflicting settings found; parent verified current official support on 2026-11-18. Client loading remains unverified.
- No prior provenance receipt is present; prior source baseline unavailable. Available source and destination compared directly; no retirements or unrelated-file changes.

## Verification

- Every listed payload path compared against the requested source and destination bytes; existing payload SHA-256 baselines and staged-file hashes recorded in the preparation manifest.
- Applicable root instructions read; no nested AGENTS.md or CLAUDE.md files found under affected infrastructure directories.
- Local Markdown links, project context pointers, client includes, all four adapter metadata pairs, canonical resources and licenses checked against a staged-over-destination view.
- Fixed Codex model/effort table and four Claude model/effort presets match the requested source. Optional project TOML parses with only the two approved executor-default settings.
- Source-only README, source root instructions, transfer procedure and scripts omitted. Product source, requirements, decisions, tasks, roadmap, status, private data, unrelated skills/presets/settings, permissions and ignores preserved.
- Parent supplied authoritative read-only Git status and HEAD `5d5276fd6c99e2384f9acdcf7a24534d150bd7b2`; existing work in README, roadmap/status, data-layout, pyproject, CLI, T004/T005, CLI tests and untracked parse implementation/tests preserved. Executor Git status itself was sandbox-blocked.
- Product tests not run: this is an instructions-only update.

## Applied Verification

- Applied on 2026-11-18 from source revision `5ab76bf2f5b726998b690b362a15c6e164f4ae85`.
- Prepared content hashes and original destination hashes matched before writing.
- Installed file bytes, local payload links/client includes, fixed model/effort tables, adapters, presets, and optional TOML defaults verified after writing.
- Git diff whitespace check for affected tracked infrastructure files passed.
- Existing unrelated modified/untracked file contents preserved (19 non-secret paths checked by hash).
- Client instruction loading, effective model execution, and quota savings: not verified.
