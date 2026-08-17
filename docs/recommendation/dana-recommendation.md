<!-- SPDX-License-Identifier: MIT -->

# Recommendation for Dana — Part 1 production platform

**Approve App Platform with managed data for the migration, defer Kubernetes,
and start local implementation now.** This is the smallest design that keeps
accepted jobs recoverable after worker or queue failure without asking a
three-engineer team to operate Kubernetes and PostgreSQL during a six-week
deadline.

Run the API and background workers on **DigitalOcean App Platform**. Store PDFs
privately in **Spaces**, keep the official job record in **managed PostgreSQL**,
and use **managed Valkey** only to move job IDs. Terraform creates foundational
resources; reviewed CI deploys the application from a versioned App Spec—not by
SSH.

**Status (2026-08-17):** The simulated application, Terraform foundations,
versioned App Specs, blocking CI, and a **live staging smoke** are built and
reachable. Staging proves upload → async job → status on real managed services.
**Production approval is not granted:** measured load, soak, rollback,
dependency failure, restore, security, and capacity-headroom evidence remain
open. See [access instructions](../evidence/access.md) and
[evidence gates](../evidence/README.md).

## What exists today—and what does not

### Built and demonstrated

- FastAPI simulation plus worker: vendor-scoped upload, PostgreSQL ledger,
  Valkey wake queue, private Spaces, async inference gateway, retries, DLQ.
- Terraform modules and staging/production roots; staging foundations applied.
- Live staging endpoint with documented temporary FakeAuth (any Bearer token
  maps to a vendor id for the exercise).
- Blocking CI: lint, strict typing, unit tests, security scans, Terraform
  validate, container image build.
- Staging smoke: `GET /healthz`, `POST /v1/contracts` → `202`, poll to
  `succeeded`. Reproducible via [access instructions](../evidence/access.md).

### Still not done (blocks production claim)

- Representative load, sustained soak, and measured monthly bill.
- Worker-kill, queue-loss, rolling deploy, rollback, restore, and failover drills
  attached as reviewed evidence.
- Real identity provider, malware-scanning product selection, and production
  `AUTH_MODE=fail_closed` on the live app.
- Production foundations apply and go-live authorization.

This submission is a **working staging exercise plus a reviewed design**, not a
production-readiness certificate.

## How the proposed system works

1. A vendor authenticates and uploads a bounded PDF.
2. The API validates the file, creates an opaque private Spaces object, and
   writes a PostgreSQL job row.
3. If policy requires scanning, the job stays quarantined and cannot be queued
   or sent to inference until a durable scanner release. Otherwise, bounded
   validation releases it immediately.
4. The API puts only the non-sensitive `job_id` into Valkey and returns
   `202 Accepted`.
5. A worker claims the job, reads the PDF, and calls DigitalOcean Serverless
   Inference through one controlled gateway.
6. The worker records every attempt and the final result in PostgreSQL before
   acknowledging the queue message.
7. If Valkey loses an item, reconciliation finds an eligible `accepted` or
   `retry` PostgreSQL row that is not leased and safely re-enqueues it.
8. The customer polls a vendor-scoped status endpoint for completion or a clear
   terminal failure.

PostgreSQL is the memory of the business. Valkey is only the conveyor belt.
Spaces is the private file cabinet. This distinction is what prevents another
queue or worker failure from silently deleting accepted jobs.

## The choices that matter and why

| Choice | Reason it matters |
|--------|-------------------|
| App Platform for API and workers | Gives health-checked rolling deployment without making this team operate Kubernetes |
| Managed PostgreSQL as the ledger | Keeps accepted jobs, attempts, and results durable; production uses a primary plus standby |
| Managed Valkey as transport only | Keeps dispatch fast while making queue loss recoverable from PostgreSQL |
| Private Spaces for PDFs | Removes customer files from temporary container disks and supports time-limited private access |
| Asynchronous `202 + job_id` API | Jobs take 20 seconds to 4 minutes; keeping an HTTP request open would be fragile |
| Server-derived `vendor_id` | Prevents one customer from selecting or reading another customer’s contracts |
| Bounded timeout and retries | Inference calls time out after 240 seconds; the initial attempt plus at most three retries means four attempts total before durable failure |
| Provisional inference cap of 10 | A PostgreSQL semaphore enforces one fleet-wide limit across all workers/releases until quota, load, and prepaid cost are measured |
| Private managed-data path | Production attaches App Platform to the approved VPC, restricts PostgreSQL/Valkey trusted sources, and uses private bindables |
| Long-job drain | Workers stop taking new work and finish or safely release in-flight jobs within the tested 600-second deployment grace |
| Terraform foundations + App Spec CI | Makes environments reproducible while keeping arbitrary runtime JSON secrets out of Terraform inputs |
| Seeded faults + Locust + scripts | Separates deterministic business-rule tests, load/soak tests, and real platform failure drills |

## Decisions still open

Working defaults (traffic shape, RPO/RTO, budget ceiling, identity, scanning,
region) are recorded in the [assumption log](../client/assumption-log.md) with
owners and close dates. Staging currently uses a **named temporary auth
exception** until Dana chooses an identity provider.

## Disagreements with Dana’s note—and why

1. **Do not use the already-provisioned Kubernetes cluster merely because it
   exists.** That is sunk cost, not evidence that the team can operate it safely
   during an enterprise migration. Reconsider DOKS only when a named platform
   owner exists or measured needs exceed App Platform.
2. **Do not put PostgreSQL in Kubernetes for Part 1.** The visible saving is
   small compared with owning replication, WAL, backup, restore, upgrades,
   failover, and on-call. One pod plus snapshots is not HA or point-in-time
   recovery.
3. **Do not treat the $15 managed PostgreSQL plan as production HA.** It is a
   useful managed staging tier; production needs a matching standby.
4. **Do not use object or block storage as a Valkey replacement.** Keep the
   durable job record in PostgreSQL and reconstruct queue work from it.
5. **Do not stay on one Compose Droplet.** It preserves the same
   API/worker/database/queue failure domain that already lost work.
6. **Do not promise automatic scaling “as needed” without a measured arrival
   rate and provider quota.** Scale from queue wait and completion evidence,
   while respecting the inference cap and budget.
7. **Do not recreate the load balancer for every release.** App Platform rolling
   deployment is simpler now; a later DOKS blue/green design should switch
   traffic behind one stable load balancer.
8. **Do not interpret “please do not 10× the bill” as approval for anything
   below $4,000.** Dana and the CTO should set a target and a hard ceiling.

## Explicit exclusions (deferred)

- Production Kubernetes and Helm.
- Self-managed production PostgreSQL or Valkey.
- Multi-region active-active deployment.
- Service mesh and Kafka.
- GPUs or self-hosted inference for Part 1.
- A real contract parser, OCR quality work, or model evaluation.
- A full observability SaaS stack; start with structured logs and essential
  metrics.
- Customer-managed encryption keys unless policy requires them.
- A selected malware-scanning product until customer policy confirms the need.

These omissions reduce delivery risk. They can be added when a measured
requirement justifies their cost and operating burden.

For the later Part 2, separately validate whether “under two seconds” means
time-to-first-token or full completion before committing to 400 concurrent
generations, 99.9% availability, and a $2,500 ceiling.

## What this should cost per month

All figures are planning estimates, not quotes. Verify current SKUs, region,
quota, and pricing before purchase.

| Item | Planning treatment |
|------|--------------------|
| Current pilot | About **$400/month** on the existing single-box setup |
| Part 1 production platform | About **$360–750/month**, excluding inference; exact worker and Valkey SKUs require load evidence |
| Staging PostgreSQL | Begins around **$15/month** for a managed 1 GiB single node; not HA and additive while staging stays online |
| Production PostgreSQL | Begins around **$60/month total** for a ~$30 2 GiB primary plus matching standby |
| Managed Valkey | HA queue/cache SKU still requires a purchase-date quote and load validation; included in the production band |
| Spaces | Begins around **$5/month** plus usage |
| Registry | Begins around **$5/month** |
| Serverless inference | Prepaid/usage-based and separate from the platform band |
| Part 2 self-hosted inference | The **$2,500/month** figure belongs to the later self-hosted-model phase, not Part 1 |

The production floor includes at least 2 API instances, 2 workers, managed
PostgreSQL HA, managed Valkey HA, private Spaces, a registry, and essential
network/observability usage.

The managed-database comparison is important: moving from a ~$15 staging node
to a ~$60 production HA pair is a visible premium of roughly $45/month. At any
loaded engineering cost above $45/hour, less than one hour of monthly database
maintenance or incident work erases that saving. Self-managed PostgreSQL would
require much more than that once patching, WAL, backups, restore drills,
monitoring, failover, and on-call are counted.

## What still worries me

1. **The forty lost jobs have no proven root cause.** The new design survives
   plausible failure points, but we should not claim to have fixed the specific
   incident until its timeline is reconstructed.
2. **“A few thousand contracts” is not capacity data.** We need the busiest
   minute/hour, PDF size distribution, desired completion window, and whether
   uploads can be paced.
3. **Identity and upload policy are unresolved.** The identity provider,
   encrypted-PDF behavior, malware scanning, retention, and residency rules can
   change the staging design.
4. **Recovery language is unresolved.** “No downtime” may mean API availability,
   or it may mean no interruption to a four-minute job; these are different
   commitments.
5. **Inference quota and cost are not measured.** A provisional cap of 10 limits
   risk but does not prove migration throughput.
6. **CPU autoscaling is a poor signal for waiting workers.** Migration capacity
   should be based on queue wait, completion rate, memory, quota, and cost.
## What Dana should do over the next six weeks

**Dana and CTO—this week:** approve the direction, set the target and maximum
monthly spend, choose the recovery target, assign decision owners, and send the
incident/security inputs. If an answer is temporary, record the owner and expiry
rather than leaving it implicit.

| Week | Dana / CTO action | Engineering action | Exit evidence |
|------|-------------------|--------------------|---------------|
| 0 — now | Approve direction; set target/hard budget ceiling and RPO/RTO; assign owners; provide incident/security inputs | Publish this recommendation; keep staging access documented | Written decisions or named temporary assumptions |
| 1 | Choose identity provider or extend the staging-auth exception with expiry | Flip staging toward real auth; vendor-isolation tests on live stack | IdP path chosen; cross-vendor denial evidenced |
| 2 | Confirm migration arrival/pacing and representative PDFs | Locust load/soak; timeout/retry/DLQ and queue-loss tests | Measured throughput, p95 queue wait, error rate |
| 3 | Approve production spend/region if evidence supports sizing | Production Terraform prep (human-gated); chaos drills (worker kill, deploy drain) | Drill logs + job timelines attached |
| 4 | Attend recovery/security review | PostgreSQL restore and standby failover rehearsal; rollback rehearsal | Restore/failover/rollback evidence attached |
| 5 | Approve migration pace, support window, rollback authority | Cost/headroom report; runbooks with named owners | All applicable readiness gates pass |
| 6 | Authorize go-live only if evidence passes | Freeze known-good image/config; paced migration; monitor | Go/no-go record and retained rollback |

Production approval requires passing the binary gates in
[evidence/README.md](../evidence/README.md). Staging smoke alone is not enough.

## Supporting detail

This document is intended to stand alone. The following provide implementation
and audit detail:

- [Part 1 architecture](../architecture/part1-production-platform.md)
- [Part 2 AI design](../architecture/part2-self-hosted-inference.md)
- [Decision record](../decisions/ADR-001-part1-platform.md)
- [Assumption log](../client/assumption-log.md)
- [Clarification checklist](../client/clarification-checklist.md)
- [Recovery trade-offs](../architecture/tradeoffs-rpo-rto.md)
- [Evidence plan](../evidence/README.md)
