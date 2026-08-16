<!-- SPDX-License-Identifier: MIT -->

# Trade-offs: recovery targets (RPO / RTO)

**Audience:** Dana and CTO. Choose one envelope before calling the platform
“production-ready” for enterprise migration.

**Plain language:**

- **How much work might we ask customers to resend?** (RPO — recovery point)
- **How long might uploads/processing be unavailable?** (RTO — recovery time)

Show this table in the clarification workshop before locking ADR-001.

---

## Three envelopes

| Envelope | Meaning in practice | What we buy / operate | Monthly cost impact (platform, excl. inference) | When to choose |
|----------|---------------------|------------------------|--------------------------------------------------|----------------|
| **Conservative production** (scaffold default) | Lose at most ~15 minutes of *uncommitted* work; be back within ~60 minutes after a serious failure. PDFs live in Spaces; job records in managed Postgres with backups/PITR where available. | Managed PostgreSQL HA + PITR, Spaces, ≥2 API + ≥2 workers, tested restore drill | Lowest *correct* ops load for enterprise; typically within ~1–2× today’s $400 if sized modestly | Default planning baseline until Dana states SLA |
| **Aggressive HA** | Near-zero acceptable data loss; back within ~15 minutes. Tighter failover, more redundancy, more drills. | Larger HA DB SKUs, stricter runbooks, possibly multi-AZ patterns within DO product limits, more frequent restore tests | Higher managed SKUs + engineering time | Only if written enterprise SLA demands it |
| **Cutover blocked** | Targets unresolved — we will not put your name on a production cutover claim. | Keep building scaffolding and evidence design; no “ready for biggest customer” assertion | Avoids false confidence | If Dana cannot state RPO/RTO or SLA text |

DigitalOcean’s **$15/month** 1 GiB managed PostgreSQL entry plan is useful for
staging and restore rehearsals, but it is a single node that DigitalOcean marks
not highly available and recommends for development/testing. The production
baseline uses at least a 2 GiB primary plus matching standby (roughly $60/month
minimum database node cost at the cited starting prices). Backups/PITR protect
recovery points; only a standby topology addresses primary-node availability.
Single-node “automatic failover” means managed replacement/recovery, not an
already-running standby and therefore not the conservative availability proof.

Citations for managed durability features:
[PostgreSQL features](https://docs.digitalocean.com/products/databases/postgresql/details/features/),
[PostgreSQL pricing](https://docs.digitalocean.com/products/databases/postgresql/details/pricing/),
[Spaces](https://docs.digitalocean.com/products/spaces/),
[Valkey limits](https://docs.digitalocean.com/products/databases/valkey/details/limits/) (no backup/restore — do not use as sole job archive).

---

## What each envelope does *not* buy

| Misconception | Reality |
|---------------|---------|
| “HA database means zero downtime forever” | Failover and maintenance can still interrupt connections; the app must retry. |
| “Redis/Valkey HA means jobs cannot be lost” | Managed Valkey has no backup/restore. Postgres must record accepted jobs. |
| “Spaces means instant multi-region DR” | Spaces is durable object storage; multi-region is a separate, costlier design we deliberately omit in Part 1. |
| “Choosing Conservative means we never lose a job in flight” | In-flight worker memory can still fail; design recovers by **requeue from Postgres** / idempotent retry. |

---

## Decision prompt for Dana

1. Pick **Conservative**, **Aggressive**, or **Blocked**.
2. Attach any enterprise SLA language that overrides the choice.
3. Confirm whether “no downtime” applies to **API availability only** or also to
   **uninterrupted long-running extraction jobs**.

Until answered, ADR-001 and Part 1 docs treat **Conservative** as assumption
`A-REL-01` only — not a customer commitment.
