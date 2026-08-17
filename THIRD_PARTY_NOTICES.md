<!-- SPDX-License-Identifier: MIT -->

# Third-Party Notices

This project's own source is MIT-licensed. It additionally vendors third-party
skills under `.ai/skills/`. Those skills retain their original licenses; this
file records their provenance and any modifications, per their license terms.

## First-party content (MIT)

All content authored in this repository is MIT-licensed (see `LICENSE`).
First-party skills declare `license: MIT` in their `SKILL.md` frontmatter; other
first-party source and docs carry an `SPDX-License-Identifier: MIT` header.

The following skills are original to this repository and licensed under MIT:

| Skill (`.ai/skills/<dir>`) | License |
|----------------------------|---------|
| `ai-engineer`              | MIT |
| `backend-architect`        | MIT |
| `clean-code`               | MIT |
| `code-reviewer`            | MIT |
| `content-marketing-expert` | MIT |
| `devops-automator`         | MIT |
| `document-skills`          | MIT (pointer-only; see below) |
| `full-stack-developer`     | MIT |
| `immersive-3d-ux`          | MIT |
| `principal-engineer`       | MIT |
| `principal-uefi-engineer`  | MIT |
| `test-quality-evaluator`   | MIT |
| `twitter-algorithm-optimizer` | MIT (clean-room; see below) |
| `memory-curator`           | MIT (clean-room; see below) |
| `contribution-summary`     | MIT (clean-room; see below) |
| `roadmap-review`           | MIT (clean-room; see below) |

Composite subagents under `.ai/subagents/` are likewise MIT, including
`memory-steward`.

## Application runtime dependencies (`app/`)

Declared in `app/pyproject.toml`. Allowed licenses only (MIT / BSD / Apache-2.0 / ISC).
Regenerate exact versions from `app/uv.lock` before release.

| Package | Purpose | License family |
|---------|---------|----------------|
| `fastapi` | HTTP API transport | MIT |
| `uvicorn` | ASGI server | BSD-3-Clause |
| `httpx` | Async inference client | BSD-3-Clause |
| `pydantic` / `pydantic-settings` | Settings and schemas | MIT |
| `sqlalchemy` | Async job ledger ORM | MIT |
| `asyncpg` | PostgreSQL driver | Apache-2.0 |
| `redis` | Valkey asyncio client | MIT |
| `boto3` | Spaces S3-compatible adapter | Apache-2.0 |
| `python-multipart` | Upload parsing | Apache-2.0 |

## Reporting tool dependencies

| Package | Purpose | License | Source |
|---------|---------|---------|--------|
| `python-pptx` | Generate the local executive-briefing PowerPoint artifact | MIT | https://github.com/scanny/python-pptx |

The briefing generator declares this tool dependency through PEP 723 metadata;
it is not an application runtime dependency.

## Vendored AI skills

The following skills were imported from
[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
and are licensed under the **Apache License 2.0**.

| Skill (`.ai/skills/<dir>`) | Upstream path | License | License file |
|----------------------------|---------------|---------|--------------|
| `changelog-generator`       | `changelog-generator`       | Apache-2.0 | repo root (Apache-2.0) |
| `content-research-writer`   | `content-research-writer`   | Apache-2.0 | repo root (Apache-2.0) |
| `developer-growth-analysis` | `developer-growth-analysis` | Apache-2.0 | repo root (Apache-2.0) |
| `file-organizer`            | `file-organizer`            | Apache-2.0 | repo root (Apache-2.0) |
| `lead-research-assistant`   | `lead-research-assistant`   | Apache-2.0 | repo root (Apache-2.0) |
| `meeting-insights-analyzer` | `meeting-insights-analyzer` | Apache-2.0 | repo root (Apache-2.0) |
| `mcp-builder`               | `mcp-builder`               | Apache-2.0 | `.ai/skills/mcp-builder/LICENSE.txt` |
| `theme-factory`             | `theme-factory`             | Apache-2.0 | `.ai/skills/theme-factory/LICENSE.txt` |
| `webapp-testing`            | `webapp-testing`            | Apache-2.0 | `.ai/skills/webapp-testing/LICENSE.txt` |

Upstream repository license: Apache-2.0
(https://www.apache.org/licenses/LICENSE-2.0).

### Modifications

The `SKILL.md` frontmatter of each vendored skill was rewritten to conform to
this project's universal skill format (`.ai/SKILL-FORMAT.md`) — adding
`aliases`, `version`, `platforms`, `scope`, `triggers`, `source`, and `license`
fields. Skill body content is unmodified. The original `name` and `description`
are preserved.

## License-incompatible upstreams — replaced with original content

The following requested skills were **not** vendored because their upstream
licenses violate `.ai/rules/security.md`. Instead, license-clean replacements
were authored in-repo (MIT) — no upstream code or text was copied:

| Skill | Upstream license | Replacement in this repo |
|-------|------------------|--------------------------|
| `document-skills` (docx, pdf, pptx, xlsx) | Proprietary (© Anthropic, all rights reserved) — forbids copying, retaining copies outside Anthropic services, and derivative works | `.ai/skills/document-skills/SKILL.md` — a **pointer-only** skill (MIT) that defers to the platform's native document skill at runtime or to permissively licensed libraries; no proprietary content vendored. |
| `twitter-algorithm-optimizer` | AGPL-3.0 (blocked copyleft) | `.ai/skills/twitter-algorithm-optimizer/SKILL.md` — a **clean-room** skill (MIT) restating publicly known ranking principles in original prose; no AGPL source reproduced. |

## Concepts referenced, no code vendored

The agentic memory primitive (`.ai/memory/`, `.ai/rules/memory.md`,
`.ai/skills/memory-curator/`, `.ai/subagents/memory-steward.md`) restates
concepts from the following public sources in original prose. No files,
code, or verbatim text were copied from any of them; no proprietary or
internal system was consulted for this content.

| Source | License / status | What was referenced |
|--------|-------------------|----------------------|
| [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) | MIT, public | Policy modes (strict/permissive/audit), "memory as context, never executable policy" |
| OWASP Agentic AI Top 10 (2026) | Public standard | Memory poisoning as a named risk category; treating retrieved memory as untrusted input |
| NIST AI Risk Management Framework | Public standard | Govern/Map/Measure/Manage framing for the governance lifecycle |
| MADR / Nygard ADR format | Public, widely used convention | `proposed`/`accepted`/`deprecated`/`superseded` status vocabulary |
| Obsidian app configuration format | Public, documented by Obsidian | `.obsidian/app.json` keys (`newLinkFormat`, `useMarkdownLinks`, etc.) |
| Cognitive-science memory taxonomy (episodic, semantic, procedural, prospective, parametric) | Public domain concepts | The five memory types and what each answers |

Two clean-room reporting skills, `contribution-summary` and
`roadmap-review`, are original implementations that read local git history
and `.ai/memory/` only — they carry no vendor branding and no dependency on
any particular issue tracker, wiki, or presentation format. Each documents
an optional, explicitly-opt-in handoff to a locally installed personal
skill with a similar name, if one happens to be present outside this
repository; no such skill is bundled with or required by this template.
