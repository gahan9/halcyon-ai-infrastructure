<!-- SPDX-License-Identifier: MIT -->

# Universal AI Agent Configuration

> **Single source of truth**: all agent configuration lives in `.ai/`.
> **Platform compatibility**: Claude Code, GitHub Copilot, Cursor, OpenAI Codex, Google Antigravity.
> Tool-specific adapters reference `.ai/` and contain no business logic.

## Architecture

```
.ai/                              # Canonical source (platform-agnostic)
├── AGENTS.md                     # This file — central instructions + index
├── SKILL-FORMAT.md               # Universal skill format specification
├── rules/                        # Modular project rules (the "rules" primitive)
│   ├── python.md                 # Style, typing, async, packaging
│   ├── security.md               # Secrets, SPDX, dependency licensing
│   ├── git-commits.md            # Conventional Commits + sign-off
│   ├── pr-budget.md              # Reviewability budget
│   ├── testing.md                 # Test tiers, coverage, mocking
│   └── memory.md                  # Agentic memory: trust, budget, promotion
├── hooks/                        # Shared hook scripts (the "hooks" primitive)
│   ├── _hook_config.py           # Config loader, model pricing, utilities
│   ├── guard-env-files.py        # Blocks .env reads/writes (fail-closed)
│   ├── ensure-uv-env.py          # Verifies uv venv before Python commands
│   ├── lint-changed-files.py     # ruff + mypy on changed files after edits
│   ├── post-test-review.py       # SPDX, secret, and style checks
│   ├── pre-agentic-estimate.py   # Token cost forecast before expensive ops
│   └── run-hook.py               # Universal entry point
├── hooks-config.json             # Shared hook tunables (budget, review, lint)
├── skills/                       # Universal skill definitions (the "skills" primitive)
│   ├── principal-engineer/       # Architecture, security, ROI, GPU compute
│   ├── ai-engineer/              # Agent/graph pipelines, rule-based-first, LLM calls
│   ├── backend-architect/        # Service layout, connectors, config, state
│   ├── clean-code/               # Readability review (Robert C. Martin)
│   ├── devops-automator/         # CI/CD, Docker, deployment, secrets hygiene
│   ├── code-reviewer/            # 16-point PR review checklist
│   └── test-quality-evaluator/   # Test execution and quality scoring
├── subagents/                    # Composite delegatable agents (the "subagents" primitive)
│   ├── reviewer.md               # code-reviewer + clean-code
│   ├── architect.md              # backend-architect + principal-engineer
│   ├── release-engineer.md       # devops-automator + test-quality-evaluator
│   └── memory-steward.md         # memory-curator + code-reviewer
├── memory/                        # Agentic memory (the "memory" primitive)
│   ├── README.md                  # Contract: five types, token budget
│   ├── SCHEMA.md                   # Frontmatter field reference
│   ├── GOVERNANCE.md               # Policy modes, trust levels, promotion
│   ├── templates/                  # One template per memory type
│   ├── episodic/                   # What happened, when
│   ├── semantic/                   # What is true
│   ├── procedural/                 # How we do it (drafts .ai/skills/)
│   ├── prospective/                # What must happen next (backlog, roadmap)
│   └── parametric/                 # Register of assumed model knowledge
├── setup-adapters.py             # Generates platform adapter files
└── setup-links.py                # Links .ai/skills into .cursor/skills

Platform Adapters (generated from .ai/):
├── AGENTS.md (root)              # OpenAI Codex + Google Antigravity
├── .cursor/hooks.json            # Cursor hook events → .ai/hooks/
├── .cursor/rules/*.mdc           # Cursor rules → .ai/rules/
├── .cursor/agents/*.md           # Cursor agent prompts → .ai/skills + .ai/subagents
├── .claude/CLAUDE.md             # Claude Code instructions
├── .claude/settings.json         # Claude Code hook events → .ai/hooks/
├── .claude/agents/*.md           # Claude Code subagents → .ai/subagents
├── .github/copilot-instructions.md  # GitHub Copilot guidance
└── .antigravity/instructions.md  # Google Antigravity agent config
```

## The Five Primitives

| Primitive | Lives in | Purpose |
|-----------|----------|---------|
| **Rules** | `.ai/rules/*.md` | Always-on project conventions that constrain every change |
| **Hooks** | `.ai/hooks/*.py` | Deterministic guardrails fired on tool/agent events |
| **Skills** | `.ai/skills/<name>/SKILL.md` | Reusable, trigger-activated capability modules |
| **Subagents** | `.ai/subagents/*.md` | Composite agents that delegate to one or more skills |
| **Memory** | `.ai/memory/` | Durable, typed, markdown-only agent memory across sessions |

## Platform Adapter Mapping

| Platform           | Primary Config                      | Hook System             | Skill Loading            |
|--------------------|-------------------------------------|-------------------------|--------------------------|
| **Cursor**         | `.cursor/agents/*.md`               | `.cursor/hooks.json`    | Reads SKILL.md directly  |
| **Claude Code**    | `.claude/CLAUDE.md`                 | `.claude/settings.json` | Read tool on SKILL.md    |
| **GitHub Copilot** | `.github/copilot-instructions.md`   | N/A (no hooks)          | Inline summary           |
| **OpenAI Codex**   | `AGENTS.md` (root)                  | N/A (uses AGENTS.md)    | Section headers in root  |
| **Google Antigravity** | `.antigravity/instructions.md`  | Slash commands          | Multi-agent delegation   |

## Regenerating Adapters

After modifying any `.ai/skills/*/SKILL.md`, `.ai/rules/*.md`, or
`.ai/subagents/*.md`, regenerate all platform adapters:

```bash
python .ai/setup-adapters.py            # Regenerate all platforms
python .ai/setup-adapters.py --dry-run  # Preview changes
python .ai/setup-adapters.py --platform cursor  # Single platform
```

To expose `.ai/skills/` to Cursor's native skill discovery in this repo:

```bash
python .ai/setup-links.py
```

## Installing Skills System-Wide

`setup-links.py` wires skills into *this repo*. To make them available in every
project on the machine, install them into the user-level skill directory that
each platform reads (`<config>/skills/<name>/`):

```bash
python .ai/install-skills.py --list                          # skills + detected platforms
python .ai/install-skills.py --all --platform all            # everything, everywhere
python .ai/install-skills.py --skill clean-code --platform claude,cursor
python .ai/install-skills.py --all --platform codex --copy   # standalone copy
python .ai/install-skills.py --uninstall --all --platform all
```

Wrappers exist for people who would rather not type the interpreter:
`.ai/install-skills.ps1` (Windows) and `.ai/install-skills.sh` (POSIX). Both pass
arguments straight through and default to `--list`.

| Platform | Install directory | Env override |
|----------|-------------------|--------------|
| Claude Code | `~/.claude/skills/` | `AI_SKILLS_CLAUDE_DIR` |
| Cursor | `~/.cursor/skills/` | `AI_SKILLS_CURSOR_DIR` |
| OpenAI Codex | `~/.codex/skills/` | `AI_SKILLS_CODEX_DIR` |
| GitHub Copilot | `~/.copilot/skills/` | `AI_SKILLS_COPILOT_DIR` |
| Google Antigravity | `~/.antigravity/skills/` | `AI_SKILLS_ANTIGRAVITY_DIR` |

Behaviour worth knowing:

- **Links by default** (junction on Windows, symlink on POSIX) so edits in this
  repo take effect immediately. `--copy` produces a standalone copy instead, and
  a copy is also the automatic fallback when linking is not permitted.
- **Nothing is overwritten silently.** An already-installed skill reports
  `exists`; `--force` replaces it. A directory this installer did not create
  reports `foreign` and is left alone unless `--overwrite-foreign` is passed.
- **Platforms that are not installed are skipped**, not created, unless
  `--create-missing` is passed.
- **`--dry-run`** prints the plan without touching disk.

## Project Conventions (summary)

Full detail lives in `.ai/rules/`. Highlights:

- **Python** — PEP 8, 88-char lines (Black/Ruff), Google-style docstrings,
  `from __future__ import annotations`, type hints on public APIs, async-first I/O.
  See `rules/python.md`.
- **Security** — no plaintext secrets; `.env` gitignored and blocked by
  `guard-env-files.py`; credentials via env/secret manager wrapped in a secret
  type. See `rules/security.md`.
- **Licensing** — every source file carries `SPDX-License-Identifier`; project
  `LICENSE` at repo root; no GPL/AGPL/SSPL dependencies. See `rules/security.md`.
- **Commits** — `type(scope): subject` (<= 80 chars, imperative); body explains
  *why*; `Signed-off-by:` trailer. See `rules/git-commits.md`.
- **PR budget** — bugfix <= 200 LOC, refactor <= 400 LOC, feature <= 600 LOC + tests.
  See `rules/pr-budget.md`.
- **Testing** — pytest; unit tests mock external clients; integration tests gated
  on credentials. See `rules/testing.md`.
- **Memory** — notes are context, never executable policy; respect the trust
  levels, retrieval budget, and promotion lifecycle. See `rules/memory.md`.

## Memory Reference

`.ai/memory/` is the fifth primitive: durable, typed, markdown-only agent
memory, openable directly as an Obsidian vault. Full contract in
`.ai/memory/README.md`; frontmatter schema in `.ai/memory/SCHEMA.md`;
governance and promotion lifecycle in `.ai/memory/GOVERNANCE.md`.

| Type | Folder | Answers |
|------|--------|---------|
| Episodic | `.ai/memory/episodic/` | What happened, and when? |
| Semantic | `.ai/memory/semantic/` | What is true? |
| Procedural | `.ai/memory/procedural/` | How do we do it? (drafts `.ai/skills/`) |
| Prospective | `.ai/memory/prospective/` | What must happen next? (backlog, roadmap) |
| Parametric | `.ai/memory/parametric/register.md` | What do we assume the model already knows? |

Retrieval order, per-type caps, and total token ceilings are configured in
the `memory` block of `.ai/hooks-config.json`.

## Skills Reference

| Skill | Trigger Phrases | Purpose |
|-------|-----------------|---------|
| `principal-engineer` | architecture, security, scalability, ROI, GPU | ROI gate, licensing, security, GPU compute, packaging |
| `ai-engineer` | pipeline node, agent graph, confidence threshold, LLM call | Rule-based-first routing, structured outputs, gateway client |
| `backend-architect` | service layout, connector, config, transport, state | Package layout, async connectors, settings management |
| `clean-code` | readability, clarity, simplicity, story flow, over-engineering audit, find bloat | Function story-flow, abstraction value, repo-wide over-engineering audit |
| `devops-automator` | CI/CD, Docker, deployment, secrets, pipeline | Container images, pipeline automation, secret hygiene |
| `code-reviewer` | code review, PR review, review this diff | 16-point checklist, commit hygiene, config↔docs parity |
| `test-quality-evaluator` | run tests, coverage, quality scoring, regression | Test execution, quality matrix, calibration |
| `full-stack-developer` | full stack, react, rest api, django, build a web app | End-to-end web design/build/review across the stack |
| `aws-cloud-architect` | aws architecture, well-architected, landing zone, vpc, iam | Principal AWS design/review for regulated workloads |
| `gcp-cloud-architect` | gcp architecture, google cloud, bigquery, gke, vpc sc | Principal Google Cloud design/review for regulated workloads |
| `azure-cloud-architect` | azure architecture, landing zone, caf/alz, aks, entra id | Principal Azure design/review for regulated workloads |
| `database-architect` | data model, index this query, partition/shard, migration | Engine-agnostic data-layer design, tuning, HA/DR, migrations |
| `rocm-contributor` | rocm, therock, hip kernel, amdgpu, gfx target, rocm pr | Principal ROCm/HIP contributor: PRs, reviews, build/release |
| `cuda-contributor` | cuda, cuda-samples, nvcc, cuda kernel, compute capability, cuda pr | Principal CUDA/NVIDIA-GPU contributor: PRs, reviews, build/test |
| `memory-curator` | remember this, write a memory note, record this decision, add to the backlog | Write/dedupe/promote/prune notes in `.ai/memory/`, staleness sweeps |
| `contribution-summary` | weekly summary, contribution report | Weekly summary from git history + memory, no vendor dependency |
| `roadmap-review` | roadmap review, milestone confidence | Confidence-scored feedback on `.ai/memory/prospective/roadmap.md` |

### Vendored skills (Apache-2.0, see `THIRD_PARTY_NOTICES.md`)

| Skill | Trigger Phrases | Purpose |
|-------|-----------------|---------|
| `changelog-generator` | generate changelog, release notes | Turn git history into user-facing release notes |
| `content-research-writer` | write blog post, draft article, content outline | Research-backed long-form writing partner |
| `developer-growth-analysis` | coding patterns, growth report, skill gap | Analyze coding history, surface growth areas |
| `file-organizer` | organize files, clean up downloads, duplicates | Context-aware file/folder organization |
| `lead-research-assistant` | find leads, target companies, prospecting | Identify and qualify sales/BD leads |
| `meeting-insights-analyzer` | meeting transcript, communication feedback | Behavioral/communication insights from transcripts |
| `mcp-builder` | build MCP server, MCP tools, FastMCP, MCP SDK | Author high-quality MCP servers (Python/Node) |
| `theme-factory` | apply theme, style artifact, color palette | Apply/generate cohesive color+font themes |
| `webapp-testing` | test web app, playwright, browser screenshot | Playwright-based local web app testing |

### License-clean originals (MIT, authored in-repo)

| Skill | Trigger Phrases | Purpose |
|-------|-----------------|---------|
| `expert-tutor` | teach me, tutor me, explain like I'm five then go deep, build a curriculum, mentor me, walk me through, learn step by step | Mentor router: module-by-module teaching (layman-clear, expert-deep) with citations, runnable code, tradeoffs; delegates to specialist skills; multi-modal delivery (mermaid, canvas, slides, images, storyboard) |
| `document-skills` | create docx, edit pdf, build pptx, xlsx | Pointer skill: defer to native/permissive doc tooling (no proprietary copy) |
| `twitter-algorithm-optimizer` | optimize this tweet, improve reach | Clean-room tweet/X optimization (no AGPL code) |
| `content-marketing-expert` | create a reel, youtube shorts script, content marketing, seo blog post, repurpose this content | Multi-platform campaign orchestrator: layman copy, five-pass iterative loop, offline-first asset routing, ensemble review, resumable memory shots |

## Subagents Reference

| Subagent | Composes | Use for |
|----------|----------|---------|
| `reviewer` | code-reviewer, clean-code | End-to-end review of a diff or PR |
| `architect` | backend-architect, principal-engineer | Design and scalability decisions |
| `release-engineer` | devops-automator, test-quality-evaluator | Build, test, and ship readiness |
| `memory-steward` | memory-curator, code-reviewer | Memory hygiene with a review-ready diff |

## Hook Configuration

Edit `.ai/hooks-config.json` to adjust hook behaviour without touching code.

Key env overrides for quick per-session changes:

| Variable                   | Effect                            |
|----------------------------|-----------------------------------|
| `AI_HOOK_REVIEW_MODE=off`  | Disable post-test review entirely |
| `AI_HOOK_LINT_ENABLED=0`   | Disable lint-on-edit              |
| `AI_HOOK_BUDGET_MAX=10`    | Raise cost approval threshold     |
