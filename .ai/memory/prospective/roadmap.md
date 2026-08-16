<!-- SPDX-License-Identifier: MIT -->
---
id: mem-2026-08-15-roadmap
type: prospective
title: Halcyon FDE roadmap
summary: >-
  Architecture adaptation now covers secure vendor uploads, recoverable async
  jobs, inference, and deterministic faults; client decisions still block
  implementation and all production-evidence gates.
created: 2026-08-15T00:00:00Z
updated: 2026-08-15T15:15:00Z
review_after: 2026-09-15
status: proposed
trust: unverified
classification: public
tags: [roadmap, halcyon, digitalocean, fde]
links: ["[[backlog]]", "[[mem-2026-08-15-part1-managed-async-architecture]]"]
supersedes: ["mem-2026-08-13-roadmap"]
source: "repo://docs/recommendation/dana-recommendation.md"
owner: fde
spdx: MIT
---

# Halcyon FDE roadmap

## Milestones

| Milestone | Target | Linked backlog ids | Confidence | Notes |
|-----------|--------|----------------------|------------|-------|
| Design scaffold + client checklist | 2026-08-15 | halcyon-001 | High | Done this phase |
| Primary-requirement architecture adaptation + executive brief | 2026-08-15 | halcyon-006 | High | Done; proposed pending human review |
| Dana answers + ADR-001 accepted | 2026-08-22 | halcyon-002 | Unknown | Blocks implement |
| Sim app + Terraform + staging evidence | 2026-09-05 | halcyon-003, halcyon-007 | Unknown | After checklist; 7 readiness gates currently FAIL |
| Enterprise migration support window | ~six weeks from kickoff | halcyon-004 | Unknown | Depends on load answers |
| Part 2 self-host design lock | ~+6 months | halcyon-005 | Low | Needs §F disambiguation |

## Links

- [[backlog]]
- [[mem-2026-08-15-part1-managed-async-architecture]]
