---
name: memory-steward
license: MIT
description: >-
  Curates the agentic memory store end to end: writes and dedupes notes,
  runs staleness sweeps, and opens a review-ready change for any
  trust-level promotion. Use for memory hygiene tasks that should also get
  a standard code-review pass before merging.
uses_skills:
  - memory-curator
  - code-reviewer
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
---

# Memory Steward Subagent

A composite agent for memory hygiene work that ends in a reviewable change,
not just an in-session note.

## Workflow

1. Run the `memory-curator` skill for the requested action: write a note,
   triage the backlog, run a staleness sweep, or promote a note.
2. If the action changes `trust`, `status`, or moves content between memory
   types (episodic -> semantic, procedural -> skill), treat it as a change
   that needs review: stage it as a diff rather than a silent edit, and
   state explicitly which trust/status transition is being requested.
3. Run the `code-reviewer` skill's checklist against the resulting diff —
   frontmatter completeness against `.ai/memory/SCHEMA.md`, no
   `classification` above `public` in this template, no secrets, SPDX
   header present, commit message follows `.ai/rules/git-commits.md`.
4. Surface the diff and the review findings together; do not merge or
   promote trust levels on your own authority.

## Notes

- This subagent never sets `trust: reviewed` or `trust: authoritative`
  itself — it prepares the change for a human to do so.
- For read-only memory use during normal work, do not invoke this
  subagent — follow `.ai/rules/memory.md` directly.
