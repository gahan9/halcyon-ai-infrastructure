<!-- SPDX-License-Identifier: MIT -->

# ADR-001 — Part 1 production platform

- **Status:** Proposed (scaffold) — pending Dana confirmation of budget, RPO/RTO, and incident forensics
- **Date:** 2026-08-15
- **Deciders:** FDE recommendation for Dana / CTO; ensemble reviewers Composer 2.5, GPT-5.6 Sol, Grok 4.6 (Claude Opus 5 unavailable)

## Context

Halcyon Labs runs API + worker + Postgres + Redis on one Droplet via Docker
Compose. They have enterprise customers arriving in ~six weeks, prior OOM that
lost ~40 jobs, SSH-based deploys with ~30s API downtime, hung model calls, a
provisioned but unused DOKS cluster, ~$400/month spend, runway concerns, and no
infrastructure specialist.

The exercise requires infrastructure that comes up from code in a clean
DigitalOcean account. The application is a simulation, not a real contract
parser. DigitalOcean Serverless Inference is required for Part 1 model calls
([Inference docs](https://docs.digitalocean.com/products/inference/);
OpenAI-compatible endpoint `https://inference.do-ai.run`).

## Decision

**Adopt Option B for Part 1:**

1. **DigitalOcean App Platform** for the HTTP API and asynchronous workers
2. **Managed PostgreSQL** as the authoritative job ledger (accepted jobs,
   attempts, status, results)
3. **Managed Valkey** as the work queue / cache only — never sole durability
4. **Spaces** for durable private storage of uploaded PDFs
5. **Terraform + versioned App Spec + CI image promotion** instead of SSH
   `docker compose` deploys
6. **Defer DOKS** for production workloads until reopen triggers fire
7. Use a **240-second inference timeout** and a provisional application-level
   ceiling of **10 fleet-wide in-flight inference calls**, pending provider quota
   verification and load evidence
8. Allow the initial attempt plus at most **three retries**, then persist
   `dead_letter` and report terminal failure
9. Require App Platform VPC attachment, restricted managed PostgreSQL/Valkey
   trusted sources, and verified private database endpoints before production;
   Spaces remains private through ACLs, scoped credentials, and TLS
10. Permit vendor-authorized, GET-only Spaces S3-compatible presigned URLs with
    one-hour default and ≤24-hour maximum; URL expiry does not replace object
    retention policy

## Non-negotiable application controls (any platform)

- Asynchronous ingest (`202` + job id); do not block HTTP on 20s–4m extraction
- Derive `vendor_id` from the authenticated principal; never trust
  client-supplied ownership, filenames, or object keys
- Validate bounded PDF input and keep objects private/quarantined until required
  security checks pass
- Write job row to Postgres **before** relying on the queue
- Bounded inference timeout, jittered retries, dead-letter queue
- Idempotent workers; recover abandoned jobs from Postgres
- Enforce the provisional fleet inference cap with a runtime PostgreSQL
  advisory-lock semaphore across all replicas and overlapping releases
- PostgreSQL is the Valkey outage fallback through reconciliation; Block
  Storage and Spaces never substitute for queue or job-ledger semantics
- Do not treat one PostgreSQL pod, a PVC, or CSI snapshots as production HA,
  PostgreSQL-consistent backup, or PITR
- Seeded timeout/failure simulation in tests/staging only; production rejects
  non-zero simulation rates
- Worker termination grace ≥ worst-case job (configure up to 600s on App
  Platform — [termination docs](https://docs.digitalocean.com/products/app-platform/how-to/configure-termination/))
- ≥2 API instances and ≥2 worker instances for rolling deploys
- No secrets in git; inject via platform/secret store; `.env.example` only

## Consequences

### Positive

- Isolates fat PDF / worker memory pressure from the API
- Managed Postgres HA/PITR reduces “we run the database ourselves” risk
  ([features](https://docs.digitalocean.com/products/databases/postgresql/details/features/))
- Vendor-scoped authorization and private object keys make tenant isolation an
  explicit acceptance test instead of an implicit filename convention
- Replaces night SSH deploys with rolling, health-checked releases
  ([deployments](https://docs.digitalocean.com/products/app-platform/how-to/manage-deployments/),
  [health checks](https://docs.digitalocean.com/products/app-platform/how-to/manage-health-checks/))
- Fits a three-engineer team without inventing a platform org
- Keeps images portable for a later GPU serving cell (Part 2)

### Negative / accepted limits

- Worker autoscaling is not request-based; CPU scaling is a poor signal while
  waiting on inference — plan fixed replicas and bump for migration week
  ([limits](https://docs.digitalocean.com/products/app-platform/details/limits/))
- App Platform local disk is small and non-persistent — Spaces is mandatory
- Malware scanning/quarantine remains a blocking policy choice if enterprise
  security requires it; the simulation cannot claim that control without proof
- Less “Kubernetes demo” theater for reviewers who equate K8s with maturity

### Rejected alternatives

| Option | Verdict | Reason |
|--------|---------|--------|
| **A — DOKS + managed data** | Defer | Correct long-term shape for a platform team; unjustified six-week adoption risk with zero production K8s experience |
| **C — DOKS + in-cluster Postgres/Valkey** | Reject | Recreates fate-sharing and DIY backup/failover; false economy vs managed HA |
| One Postgres pod + PVC + seven-day CSI snapshots | Exercise only | Demonstrates persistence but provides neither database HA nor automatically consistent backups/PITR |
| Valkey fallback to Block Storage / Spaces | Reject | Wrong abstraction; PostgreSQL already provides durable job reconciliation |
| Required Terraform load-balancer replacement for blue/green | Reject for Part 1 | App Platform rolling promotion is simpler; DOKS should retain one LB and switch Service/Ingress routing |
| Stay on single Compose Droplet | Reject | Already failed under load; cannot meet enterprise deploy/reliability expectations |

## Reopen triggers (move toward Option A)

Any of:

1. Halcyon hires or assigns a platform owner who has run Kubernetes in production
2. Measured need for queue-depth / custom-metrics autoscaling App Platform cannot provide
3. Service count / policy requirements exceed App Platform comfort
4. Part 2 GPU serving is proven to need DOKS node pools rather than a GPU Droplet cell
5. Compliance controls that App Platform cannot meet

## Cost note

Present low/base/high Part 1 platform estimates separately from inference token
spend. Observed $400/month is not a license to spend $4,000; every increment
must map to a removed risk. Verify SKUs on purchase date via DigitalOcean
pricing pages cited in
[tradeoffs-compute-platform.md](../architecture/tradeoffs-compute-platform.md).

Use the managed PostgreSQL 1 GiB shared single-node entry plan (published from
$15/month) for staging only. DigitalOcean marks it not HA and recommends it for
development/testing. Production keeps a managed primary + standby baseline
(published starting around $60/month total for matching 2 GiB nodes) unless an
explicit risk acceptance lowers the availability target. Self-managed
PostgreSQL remains rejected because its lower visible line item excludes
replication, backup/PITR, restore, patching, monitoring, failover, and on-call
ownership.

## References

- Ensemble summary: [tradeoffs-compute-platform.md](../architecture/tradeoffs-compute-platform.md)
- Recovery envelopes: [tradeoffs-rpo-rto.md](../architecture/tradeoffs-rpo-rto.md)
- Assumptions: [../client/assumption-log.md](../client/assumption-log.md)
- DOKS exercise alternative: [../architecture/doks-exercise-variant.md](../architecture/doks-exercise-variant.md)
- Terraform App resource: https://docs.digitalocean.com/reference/terraform/reference/resources/app/
