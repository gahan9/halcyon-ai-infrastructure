<!-- SPDX-License-Identifier: MIT -->
---
id: mem-2026-08-15-backlog
type: prospective
title: Local work backlog
summary: >-
  Architecture adaptation and executive brief are complete; client decisions,
  secure-upload policy, implementation, and seven production-evidence gates
  remain before Part 1 readiness.
created: 2026-08-15T00:00:00Z
updated: 2026-08-15T15:15:00Z
review_after: 2026-09-15
status: proposed
trust: unverified
classification: public
tags: [backlog, prospective, halcyon]
links: ["[[roadmap]]", "[[mem-2026-08-15-part1-managed-async-architecture]]", "[[mem-2026-08-15-part1-plan-review]]"]
supersedes: ["mem-2026-08-13-backlog"]
source: "repo://docs/client/clarification-checklist.md"
spdx: MIT
---

# Local work backlog

## Columns

- `id` — short kebab-case identifier, unique within this file.
- `title` — one line.
- `type` — `bug`, `feature`, `chore`, or `roadmap`.
- `priority` — `p0` (drop everything) through `p3` (someday).
- `status` — `open`, `in-progress`, `blocked`, or `done`.
- `owner` — free text; blank if unassigned.
- `issue` — GitHub Issue URL if mirrored, blank otherwise.
- `note` — optional link to a longer prospective note.

## Backlog

| id | title | type | priority | status | owner | issue | note |
|----|-------|------|----------|--------|-------|-------|------|
| halcyon-001 | Design scaffold (docs + stubs + skills) | chore | p0 | done | fde | | |
| halcyon-002 | Collect Dana checklist answers; lock RPO/RTO + budget | roadmap | p0 | blocked | dana | | [[roadmap]] |
| halcyon-003 | Implement secure async sim app + Terraform + staging evidence pack | feature | p1 | blocked | fde | | blocked on halcyon-002 and halcyon-007 |
| halcyon-004 | Enterprise migration support / paced cutover | roadmap | p1 | open | | | |
| halcyon-005 | Part 2 self-host design lock after §F disambiguation | roadmap | p2 | open | | | |
| halcyon-006 | Adapt architecture and executive brief to five primary requirements | chore | p0 | done | fde | | [[mem-2026-08-15-part1-managed-async-architecture]] |
| halcyon-007 | Confirm identity provider, upload limits, quarantine/scanner, and retention policy | roadmap | p0 | blocked | dana + security | | blocked on checklist §E |
| halcyon-008 | Pass load, soak, rollback, dependency, restore, security, and capacity gates | roadmap | p0 | blocked | engineering | | blocked on halcyon-003 |

## Links

- [[roadmap]]
- [[mem-2026-08-15-part1-managed-async-architecture]]
- [[mem-2026-08-15-part1-plan-review]]
