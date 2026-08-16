---
name: roadmap-review
license: MIT
aliases: [roadmap-feedback]
version: "1.0.0"
description: >-
  Assess milestone confidence and give feedback on
  .ai/memory/prospective/roadmap.md using deterministic scoring from
  blocker count and completion percentage. No issue-tracker or
  presentation-tool dependency. Use when asked to review, assess, or give
  feedback on the roadmap.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - ".ai/memory/prospective/roadmap.md"
  - ".ai/memory/prospective/backlog.md"
triggers:
  - "review the roadmap"
  - "roadmap feedback"
  - "assess milestone confidence"
delegates_to:
  - memory-curator
---

# Roadmap Review

## Purpose

Give deterministic, confidence-scored feedback on
`.ai/memory/prospective/roadmap.md`, grounded in the local backlog rather
than a specific issue tracker's live data.

## When to Use

- Asked to review, assess, or give feedback on the roadmap.
- Before a milestone deadline, to flag at-risk items early.

## When NOT to Use

- If there is no `roadmap.md` yet — offer to create one from
  `.ai/memory/templates/prospective.md` instead of reviewing nothing.
- If the user wants a specific branded deliverable from a locally installed
  personal skill (commonly named something like `pm-roadmap-builder`) — see
  "Optional handoff" below.

## Instructions

### Step 1 — Read inputs

1. Read `.ai/memory/prospective/roadmap.md` for the milestone table.
2. Read `.ai/memory/prospective/backlog.md` and count, per milestone: total
   items, `status: done`, `status: blocked`.
3. Read any linked `prospective/mem-*.md` notes for milestones that have
   one, for the `## Trigger` and `## Owner` sections.

### Step 2 — Score confidence (deterministic, not judgment)

| Signal | Confidence |
|--------|------------|
| 0 blocked items, >= 80% of linked backlog items done | High |
| 1-2 blocked items, or 50-79% done | Medium |
| 3+ blocked items, or < 50% done, or `review_after` already passed | Low |

Do not override this table with a subjective read of "how things feel."
If the signal is ambiguous (e.g. no linked backlog items at all), say so
and mark confidence `Unknown` rather than guessing.

### Step 3 — Write feedback

For each milestone: state its confidence, the one or two backlog items
driving it (by `id`), and one concrete next action if confidence is Medium
or Low. Skip commentary on milestones already at High confidence beyond
confirming them.

### Step 4 — Persist and present

1. Update `roadmap.md`'s confidence column in place via `memory-curator`.
2. Present the same feedback to the user as a short markdown table plus,
   only for Low-confidence milestones, one sentence of recommended action.

### Optional handoff to a locally installed personal skill

If the user has a personal, locally installed skill with a similar name and
explicitly asks for its specific output (e.g. a branded slide or a wiki
page), hand off to it explicitly and pass this skill's Step 1/2 output as
input. Do not invoke an external skill the user did not name. This template
ships no such skill and has no dependency on one.

## Output Format

```markdown
# Roadmap Review — <date>

| Milestone | Confidence | Driving items | Next action |
|-----------|------------|----------------|---------------|
| <name> | High/Medium/Low/Unknown | id1, id2 | <blank if High> |
```

## References

- `.ai/memory/prospective/README.md`, `roadmap.md`, `backlog.md`.
- `.ai/skills/memory-curator/SKILL.md` — used to persist updates.
