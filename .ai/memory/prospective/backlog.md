<!-- SPDX-License-Identifier: MIT -->
---
id: mem-2026-08-15-backlog
type: prospective
title: Local work backlog
summary: >-
  Staging smoke and production prep (remote state + human-gated apply) are
  ready on assumption-log defaults; Dana hard locks and seven evidence gates
  remain before Part 1 readiness.
created: 2026-08-15T00:00:00Z
updated: 2026-08-17T00:00:00Z
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
| halcyon-002 | Collect Dana checklist answers; lock RPO/RTO + budget | roadmap | p0 | blocked | dana | | Prep uses A-PROD-PREP-01 defaults; hard lock still Dana |
| halcyon-003 | Implement secure async sim app + Terraform + staging evidence pack | feature | p1 | in-progress | fde | | Staging smoke done; production prep scripts ready |
| halcyon-004 | Enterprise migration support / paced cutover | roadmap | p1 | open | | | |
| halcyon-005 | Part 2 self-host design lock after §F disambiguation | roadmap | p2 | open | | | |
| halcyon-006 | Adapt architecture and executive brief to five primary requirements | chore | p0 | done | fde | | [[mem-2026-08-15-part1-managed-async-architecture]] |
| halcyon-007 | Confirm identity provider, upload limits, quarantine/scanner, and retention policy | roadmap | p0 | blocked | dana + security | | Prep uses fail_closed + scan off |
| halcyon-008 | Pass load, soak, rollback, dependency, restore, security, and capacity gates | roadmap | p0 | blocked | engineering | | blocked on measured staging evidence |
| halcyon-009 | Production Terraform remote state + human-gated apply path | chore | p0 | done | fde | | docs/operations/production-prep.md |
| halcyon-010 | Mandate malware scanning on all PDF uploads | feature | p0 | open | engineering | | |
| halcyon-011 | Implement least-privilege API keys for API and Worker (IAM separation) | feature | p1 | open | engineering | | |
| halcyon-012 | Make inference concurrency cap dynamically configurable | feature | p1 | open | engineering | | |
| halcyon-013 | Perform HA standby failover drill on true HA staging database | chore | p1 | open | engineering | | |

## Links

- [[roadmap]]
- [[mem-2026-08-15-part1-managed-async-architecture]]
- [[mem-2026-08-15-part1-plan-review]]
