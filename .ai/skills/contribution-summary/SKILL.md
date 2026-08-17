---
name: contribution-summary
license: MIT
aliases: [weekly-summary]
version: "1.0.0"
description: >-
  Generate a plain-markdown weekly contribution summary from local git
  history, .ai/memory/ episodic notes, and backlog deltas. No issue
  tracker, wiki, or presentation-tool dependency. Use when asked for a
  weekly summary, status update, or contribution report.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - ".ai/memory/episodic/**/*.md"
  - ".ai/memory/prospective/backlog.md"
triggers:
  - "weekly summary"
  - "contribution report"
  - "status update for this week"
delegates_to:
  - memory-curator
---

# Contribution Summary

## Purpose

Produce a short, metric-first weekly summary of what shipped, what moved in
the backlog, and what is at risk — sourced entirely from this repository's
git history and `.ai/memory/`. No vendor branding, no external system
credentials, no dependency on a specific issue tracker or wiki.

## When to Use

- Asked for a weekly/periodic summary, status update, or contribution
  report for this repository or project.
- Preparing input for a human-written broader update (this skill's output
  is a draft, not a final executive artifact).

## When NOT to Use

- Cross-project portfolio rollups spanning multiple repositories — out of
  scope for a single-repo template skill.
- If the user has a locally installed personal skill for this (commonly
  named something like `pm-executive-briefing`) and explicitly wants its
  branded output (e.g. a specific PPTX template) — see "Optional handoff"
  below.

## Instructions

### Step 1 — Gather signal

1. Run `git log --since="7 days ago" --oneline` (or the requested window)
   against the current branch to list commits.
2. Read `.ai/memory/episodic/*.md` notes with `created` in the window.
3. Diff `.ai/memory/prospective/backlog.md` against its state at the start
   of the window if a prior snapshot is available (e.g. via `git log -p`
   on that file); otherwise summarize current `status` counts by type.
4. Do not fabricate data. If git history or memory notes are empty for the
   window, say so plainly instead of inventing activity.

### Step 2 — Compute the summary (deterministic rules, not vibes)

Apply in order; omit a bullet if its precondition is not met:

1. **Health + volume**: `<N> commits, <M> episodic notes recorded, <K> backlog items moved to done in the last <window>.`
2. **Top outcome**: the single most consequential shipped item, phrased as
   outcome not activity — avoid "worked on X"; say what X now does.
3. **Risk or blocker**: any backlog row with `status: blocked`, or any
   `parametric/register.md` failure-log row added in the window. Omit if
   none.
4. Never use vague filler ("made progress", "continued work on"). If there
   is nothing concrete, state that explicitly.

### Step 3 — Persist and present

1. Write the summary as a new episodic note via `memory-curator`
   (`type: episodic`, `tags: [contribution-summary, weekly]`) so future
   summaries can diff against it.
2. Present the same content directly to the user as markdown — a table or
   bullets, not prose paragraphs.

### Optional handoff to a locally installed personal skill

If the user has a personal, locally installed skill with a similar name
(e.g. one that posts to a specific wiki or generates a branded slide) and
asks for that specific output, hand off to it explicitly: state that you
are delegating, and pass it this skill's Step 1/2 output as input rather
than re-deriving it. Do not silently invoke an external skill the user did
not name. This template ships no such skill and has no dependency on one.

## Output Format

```markdown
# Weekly Summary — <date range>

- <health + volume bullet>
- <top outcome bullet>
- <risk bullet, if any>

## Detail
| Commits | Episodic notes | Backlog moved | Blocked |
|---------|-----------------|----------------|---------|
| N | M | K | L |
```

## References

- `.ai/memory/README.md`, `.ai/memory/GOVERNANCE.md`.
- `.ai/skills/memory-curator/SKILL.md` — used to persist the output.
- `.ai/rules/git-commits.md` — commit message conventions this reads.
