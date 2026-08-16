<!-- SPDX-License-Identifier: MIT -->
---
id: mem-2026-08-15-part1-managed-async-architecture
type: semantic
title: Part 1 uses a managed asynchronous document-processing architecture
summary: Part 1 separates secure vendor-scoped uploads, durable job state, queue transport, workers, and inference; PostgreSQL is authoritative, Valkey is recoverable transport, and deterministic faults are prohibited in production.
created: 2026-08-15T15:15:00Z
updated: 2026-08-15T15:15:00Z
review_after: 2026-09-15
status: proposed
trust: unverified
classification: public
tags: [architecture, digitalocean, halcyon, security, async-jobs]
links: ["[[mem-2026-08-15-part1-plan-review]]", "[[roadmap]]", "[[backlog]]"]
supersedes: []
source: "repo://docs/architecture/part1-production-platform.md"
confidence: 0.9
spdx: MIT
---

# Part 1 uses a managed asynchronous document-processing architecture

## Context

The project needs to accept vendor-tagged files securely, process jobs
asynchronously, call DigitalOcean Serverless Inference, and demonstrate timeout
and failure handling without recreating the operational burden that caused the
single-Droplet incident.

## Decision / Fact

Use DigitalOcean App Platform for separate FastAPI and worker components,
private Spaces for uploaded PDFs, managed PostgreSQL for authoritative
vendor/job state and dead letters, and managed Valkey only for recoverable job-id
transport. Route inference through one configurable async HTTP gateway with an
explicit timeout.

The authenticated principal determines vendor ownership. Upload validation and
any required quarantine/scanning complete before enqueue. Fault simulation is
seeded, injectable, disabled by default, and rejected by production
configuration.

This is a proposed architecture until ADR-001 is accepted by the accountable
humans. It is not production-ready until every binary evidence gate passes.

## Consequences

- Queue loss cannot erase an accepted job because PostgreSQL remains the ledger.
- Cross-vendor isolation and malformed-upload rejection become explicit tests.
- RabbitMQ/Celery, Kafka, and DOKS remain rejected for Part 1 unless an ADR
  reopen trigger fires.
- Implementation remains blocked by traffic, recovery, budget, identity, and
  data-handling decisions.

## Links

- [[mem-2026-08-15-part1-plan-review]]
- [[roadmap]]
- [[backlog]]
