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

**Status (2026-08-16):** The architecture and delivery plan are complete enough
to start reversible local work. The application, Terraform, staging environment,
and production evidence have not been built. Paid staging and production remain
behind explicit approval and evidence gates.

## What exists today—and what does not

### Completed in this repository

- A recommended architecture and decision record for App Platform, managed
  PostgreSQL, managed Valkey, and private Spaces.
- A secure upload and vendor-isolation design: the authenticated identity,
  never a filename or form field, determines who owns a contract.
- A durable job-state design with retries, idempotency, reconciliation, and a
  dead-letter state for work that cannot complete.
- A two-part Terraform design: reusable foundation modules plus separate
  staging and production environment roots.
- A delivery design in which Terraform owns foundations and secure App Spec CI
  owns the application release and runtime secrets.
- An assumption log, client decision checklist, six-week sequence, and binary
  evidence plan for load, failures, restore, failover, rollback, and security.
- A simulation test strategy: seeded application faults for deterministic retry
  tests, Locust for staging load/soak, and guarded custom scripts for worker or
  queue failure drills.

### Not yet completed

- No FastAPI simulation or worker implementation.
- No executable Terraform modules or App Spec deployment.
- No live DigitalOcean staging or production resources.
- No measured capacity, monthly bill, restore, failover, load, soak, or rollback
  evidence.

The repository is therefore a **reviewed design scaffold**, not a deployed
platform and not a production-readiness certificate.

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

## Safe assumptions that let us proceed

These are defaults, not customer promises. Each can be changed at a defined
decision gate. Every temporary assumption must be written, assigned an owner,
and given a review/expiry date before the related change merges.

| Decision | Safe working default | Must close before | Owner |
|----------|----------------------|-------------------|-------|
| Final traffic shape | Test 2 API instances, 2 workers, concurrency 2 per worker, and fleet inference cap 10 | Production sizing and final cost | Dana + migration lead |
| Recovery target | Plan job-metadata RPO ≤15 minutes and RTO ≤60 minutes | Production approval and SLA claim | Dana + CTO |
| Budget ceiling | Plan ~$360–750/month, excluding inference | Paid production apply | CTO / budget owner |
| Identity provider | Authentication adapter; fake identity is local only | Paid staging, unless a named expiring staging-auth exception is approved | Dana + Security |
| Malware scanning | Scanner/release interface; fail closed where scanning is required | Processing real customer files | Dana + Security/Legal |
| Region/residency/encryption | Configurable region/retention; private objects and TLS | Paid staging region selection | Dana + Security/Legal |
| Database size | ~$15 single-node managed staging; managed HA production | Production apply | CTO + Engineering |
| Forty-job incident cause | Treat as unknown and survive every plausible loss point | Final incident-control claim | Dana + application engineer |

### Work that should start without waiting

1. Implement typed settings, job states, retry rules, idempotency, and the seeded
   fault policy with deterministic unit tests.
2. Implement mocked PostgreSQL, Valkey, Spaces, and inference adapters.
3. Implement the API and worker while keeping every external client behind an
   interface and every network call behind a timeout.
4. Replace the current soft-fail CI scaffold with blocking lint, strict typing,
   tests, secret scanning, dependency scanning, and image build gates.
5. Build Terraform module interfaces and validate plans without applying paid
   resources.
6. Prepare Locust scenarios and staging-only failure scripts.

This work is reversible and does not require customer data or production
credentials.

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

## TODOs

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
| 0 — now | Approve this direction; assign owners; choose recovery target and Part 1 target/hard ceiling; provide incident and security inputs | Finalize interfaces and acceptance criteria | Written decisions or explicit temporary assumptions |
| 1 | Confirm migration arrival/pacing and identity test path | Domain rules, adapters, unit tests, blocking CI, container image | Deterministic tests pass; no live-service calls in unit CI |
| 2 | Approve low-cost staging spend/region and identity provider—or a named expiring staging-auth exception | Terraform foundations, private VPC/data path, App Spec CI, clean-account staging deployment | Redacted deploy logs plus working staging authentication and private database/Valkey connectivity |
| 3 | Confirm representative PDFs and completion target | Upload/status flow, Locust load/soak, timeout/retry/DLQ and queue-loss tests | Measured throughput, p95 queue wait, error rate, and cap adherence |
| 4 | Attend recovery/security review | Worker-kill, rolling deploy, PostgreSQL restore and standby failover, vendor isolation, malformed/scanner-positive tests | Recovery, failure, and security evidence attached |
| 5 | Approve migration pace, support window, and rollback authority | Tune alerts, DLQ and restore runbooks, cost/headroom report, rollback rehearsal | All applicable readiness gates pass |
| 6 | Authorize go-live only if evidence passes | Freeze known-good image/config, execute paced migration, monitor and support | Go/no-go record and retained rollback |

## What “ready” means

The platform is not production-ready because a diagram exists or because a
staging upload succeeds. Production approval requires evidence for:

- representative load and sustained soak;
- capacity headroom within inference quota and budget;
- deterministic timeout, retry, and dead-letter behavior;
- worker death and Valkey queue-loss recovery;
- rolling deployment and rollback;
- PostgreSQL point-in-time restore and managed-standby failover;
- vendor isolation, upload validation, secret handling, and audit events;
- documented runbooks with named owners.

Missing evidence is a **FAIL**, not “not tested.” A temporary exception must
name its owner, expiry, blast radius, and compensating control.

## Plain-language glossary

- **App Platform:** DigitalOcean’s managed service for running the API and
  background workers without operating Kubernetes.
- **PostgreSQL ledger:** The authoritative database record that a job exists and
  what happened to it.
- **Valkey:** A Redis-compatible fast queue/cache. Useful for transport, not the
  only copy of customer work.
- **Spaces:** Private object storage for PDFs.
- **RPO:** The maximum recent data that might need recovery or customer
  resubmission after a serious failure.
- **RTO:** How long recovery may take.
- **HA (high availability):** A primary plus ready standby that can take over;
  a single managed node is not HA.
- **Dead letter:** A terminal job state after the allowed retries are exhausted.
- **Idempotent:** Safe to repeat without creating duplicate results.

## Supporting detail

This document is intended to stand alone. The following provide implementation
and audit detail:

- [Part 1 architecture](../architecture/part1-production-platform.md)
- [Decision record](../decisions/ADR-001-part1-platform.md)
- [Assumption log](../client/assumption-log.md)
- [Clarification checklist](../client/clarification-checklist.md)
- [Recovery trade-offs](../architecture/tradeoffs-rpo-rto.md)
- [Evidence plan](../evidence/README.md)
