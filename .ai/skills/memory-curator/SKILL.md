---
name: memory-curator
license: MIT
aliases: [memory-writer, memory-steward-skill]
version: "1.0.0"
description: >-
  Write, dedupe, promote, and prune notes in the .ai/memory/ agentic memory
  store. Applies the frontmatter schema, respects trust levels and the
  retrieval token budget, and runs staleness sweeps. Use when asked to
  remember something, record a decision, write a runbook, add a backlog
  item, or clean up stale memory.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - ".ai/memory/**/*.md"
  - ".ai/hooks-config.json"
triggers:
  - "remember this"
  - "write a memory note"
  - "record this decision"
  - "add to the backlog"
  - "clean up stale memory"
  - "promote this note"
delegates_to:
  - ai-engineer
---

# Memory Curator

## Purpose

Keep `.ai/memory/` schema-conformant, deduplicated, and appropriately
trusted. This skill is the write/curate counterpart to the read-side
retrieval budget defined in `.ai/rules/memory.md`.

## When to Use

- Asked to remember, record, or write down something for later sessions.
- Asked to add, update, or triage a backlog item in
  `.ai/memory/prospective/backlog.md`.
- Asked to promote a procedural note to a skill, or an episodic note to a
  semantic note.
- Asked to run a staleness sweep or clean up memory.

## When NOT to Use

- Reading/using memory during normal work — that is governed directly by
  `.ai/rules/memory.md`, not this skill.
- Writing application code or documentation unrelated to `.ai/memory/`.
- Generating the weekly summary or roadmap review — use
  `contribution-summary` or `roadmap-review`, which call this skill to
  persist their output as an episodic or prospective note.

## Instructions

### Writing a new note

1. Pick the correct type by asking "what question does this answer?" (see
   `.ai/memory/README.md`'s table). Do not default to episodic for
   convenience.
2. Copy the matching file from `.ai/memory/templates/`.
3. Generate `id` as `mem-YYYY-MM-DD-slug` using the current date; the
   filename stem must equal `id` exactly.
4. Fill every required field from `.ai/memory/SCHEMA.md`. Leave `trust:
   unverified` — this skill never sets `trust` to `reviewed` or
   `authoritative` itself; that requires a human review step.
5. Write `summary` last, <= 40 words, after the body is final.
6. Search existing notes for overlapping `tags` or similar `title` before
   writing. If a near-duplicate exists, update it (bump `updated`) instead
   of creating a new note.
7. Never write a per-event file into `.ai/memory/parametric/`. Append a row
   to `parametric/register.md` instead.

### Adding a backlog item

1. Append a row to `.ai/memory/prospective/backlog.md` following its
   documented columns. Do not restructure the table.
2. If the item needs more than a one-line description, write a full
   `prospective` note from the template and link it in the `note` column.
3. Only create a GitHub Issue via `.github/ISSUE_TEMPLATE/backlog-item.yml`
   if explicitly asked. Never assume issue-tracker sync is wanted.

### Promoting a note

1. Confirm the promotion criteria in `.ai/memory/GOVERNANCE.md` are met
   (e.g. a procedural note used successfully multiple times).
2. For episodic -> semantic: create the semantic note, set `links` both
   ways, leave the episodic note in place as provenance.
3. For procedural -> skill: author the `SKILL.md` per
   `.ai/SKILL-FORMAT.md`, then edit the procedural note's `## Graduation
   Criteria` section to record the promotion and date.
4. Promotion changes `trust` to `reviewed` only when a human reviewer is
   doing the promotion in the same change — flag this explicitly rather than
   setting it silently.

### Staleness sweep (on request)

1. List every note whose `review_after` date has passed.
2. For each: either re-verify and bump `updated`/`review_after`, or set
   `status: deprecated`.
3. Report the sweep result as a short table; do not silently delete notes.

### Token discipline

Before writing, check whether an equivalent note already exists (reuse over
duplication is the biggest token saving). When reporting back to the user,
quote only the `summary` and the diff, not the full note body, unless asked.

## Output Format

- New/updated note: full file content, ready to write, with valid
  frontmatter.
- Backlog change: the new/edited table row only, not the whole file.
- Staleness sweep: a markdown table of `id`, `type`, `review_after`,
  proposed action.
- Promotion: a one-line confirmation plus the two file paths touched.

## References

- `.ai/memory/README.md`, `SCHEMA.md`, `GOVERNANCE.md`.
- `.ai/rules/memory.md` — the read-side retrieval rule this skill's writes
  must stay compatible with.
- `.ai/SKILL-FORMAT.md` — target format for procedural -> skill promotion.
