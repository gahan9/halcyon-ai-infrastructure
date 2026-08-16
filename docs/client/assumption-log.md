<!-- SPDX-License-Identifier: MIT -->

# Assumption log (review with Dana)

**Rules:** Assumptions are reversible defaults, not facts. Each row has an ID,
plain-language statement, confidence, impact if wrong, owner, validation date,
and reopen trigger. Promote to `reviewed` only after Halcyon confirms.

Related: [clarification-checklist.md](clarification-checklist.md)

---

## Team and operations

### A-TEAM-01 — Prefer managed services (no infra specialist)

| Field | Value |
|-------|--------|
| **Statement** | Halcyon has no dedicated infrastructure engineer and no production Kubernetes operator. We therefore prefer **managed** database, cache/queue, and object storage so DigitalOcean handles patching, backups/failover where offered, and a large share of recovery help — instead of running Postgres/Redis on the same Droplet or inside a cluster that Halcyon’s three engineers must babysit. |
| **Confidence** | High (stated in Dana’s note) |
| **Impact if wrong** | If Halcyon hires a strong platform owner tomorrow, DOKS may become viable sooner. |
| **Owner** | FDE + Dana |
| **Validate by** | Confirm staffing plan for six weeks |
| **Reopen when** | Platform hire starts, or CTO assigns dedicated K8s ownership |

### A-TEAM-02 — Empty DOKS cluster is sunk cost

| Field | Value |
|-------|--------|
| **Statement** | The already-provisioned DOKS cluster is **not** a reason to put production on it. Keeping it idle or destroying it is fine. Using it under a six-week enterprise deadline with zero production K8s experience is the primary schedule risk. |
| **Confidence** | High |
| **Impact if wrong** | Political pressure to “use what we bought” may force Option A with extra training/time. |
| **Owner** | Dana / CTO |
| **Validate by** | Explicit go/no-go on DOKS for Part 1 |
| **Reopen when** | Platform owner exists; or queue-depth autoscaling / multi-service needs exceed App Platform |

---

## State and data safety

### A-DATA-01 — Spaces holds PDFs

| Field | Value |
|-------|--------|
| **Statement** | Private [Spaces](https://docs.digitalocean.com/products/spaces/) is the durable home for uploaded contract PDFs. Local container or Droplet disks are temporary scratch only. |
| **Confidence** | Medium-High |
| **Impact if wrong** | If residency or encryption rules forbid Spaces, redesign storage/encryption before cutover. |
| **Owner** | Dana |
| **Validate by** | Data residency + encryption answers (checklist §E) |
| **Reopen when** | Customer requires CMK, alternate region, or non-Spaces storage |

### A-DATA-02 — Managed PostgreSQL is the job ledger

| Field | Value |
|-------|--------|
| **Statement** | **Managed PostgreSQL** is the authoritative job ledger. Use the 1 GiB shared single-node plan, currently beginning around **$15/month**, for staging/exercise only; DigitalOcean marks it not HA and recommends it for development/testing. That tier buys managed patching and, subject to exact-plan verification, backups/PITR—but not standby HA. Production defaults to a managed HA topology (currently around $30/month for a 2 GiB primary plus a matching ~$30/month standby), which adds standby replication/failover. A provider’s “automatic failover” wording for single-node replacement is not equivalent to a ready matching standby. Verify [pricing](https://docs.digitalocean.com/products/databases/postgresql/details/pricing/) and [features](https://docs.digitalocean.com/products/databases/postgresql/details/features/) at purchase. |
| **Confidence** | High for direction; Medium for exact SKU/size |
| **Impact if wrong** | Unsupported extensions/residency may force self-managed PostgreSQL with a funded DBA/operations plan. Using the $15 single node in production lowers the bill but fails the planned HA posture. |
| **Owner** | FDE + Dana |
| **Validate by** | Extension/region needs; current plan availability; staging restore test; CTO review of ~$15 staging versus ~$60+ HA production and self-managed operational cost |
| **Reopen when** | CTO still mandates in-cluster Postgres after risk briefing |

### A-DATA-03 — Valkey is a queue, not the archive

| Field | Value |
|-------|--------|
| **Statement** | Managed Valkey (Redis-compatible) moves work between API and workers and may cache. It is **never** the only record that a customer job exists, because managed Valkey does **not** provide backups/restore ([Valkey limits](https://docs.digitalocean.com/products/databases/valkey/details/limits/)). |
| **Confidence** | High |
| **Impact if wrong** | If Valkey were treated as source of truth, another OOM/restart could lose jobs again. |
| **Owner** | Engineering |
| **Validate by** | Job state machine design review |
| **Reopen when** | Product requires a different broker (e.g. Postgres-only queue) |

### A-DATA-04 — Root cause of the 40 lost jobs is unknown until reconstructed

| Field | Value |
|-------|--------|
| **Statement** | Until the 40-job incident is reconstructed, its root cause is **unknown**. We cannot claim Redis, PostgreSQL, Docker, or the out-of-memory event alone caused the loss. We will design so each plausible failure mode is survivable. |
| **Confidence** | High (epistemic humility) |
| **Impact if wrong** | Forensic findings may prioritize one control (e.g. Spaces) over another. |
| **Owner** | Dana + application engineer (incident evidence); FDE (resilience design) |
| **Validate by** | Incident timeline workshop |
| **Reopen when** | Logs prove a specific failure point |

### A-DATA-05 — Vendor identity is an authorization boundary

| Field | Value |
|-------|--------|
| **Statement** | The authenticated principal determines `vendor_id`; an upload field, filename, object key, or queue payload never grants vendor ownership. PostgreSQL queries and private Spaces keys are vendor-scoped, while Valkey carries only opaque job ids. |
| **Confidence** | High for the security direction; Medium for the final identity provider |
| **Impact if wrong** | Trusting client-supplied ownership could expose one customer’s contracts to another and blocks enterprise readiness. |
| **Owner** | Dana (identity requirements) + Engineering (enforcement/tests) |
| **Validate by** | Confirm identity provider and pass cross-vendor negative tests before staging approval |
| **Reopen when** | Enterprise SSO or delegated tenant-administration requirements change the authorization model |

### A-DATA-06 — Upload validation precedes inference

| Field | Value |
|-------|--------|
| **Statement** | The API accepts only bounded PDF inputs, checks signature/type, generates opaque object keys, stores objects privately, and prevents unvalidated content from reaching inference. Malware scanning is a cutover gate if customer security policy requires it. |
| **Confidence** | Medium until checklist §E defines scanner, retention, and encryption requirements |
| **Impact if wrong** | Unsupported or malicious documents could consume resources, exploit parsers, or leak through downstream processing. |
| **Owner** | Customer security/legal owner + Engineering |
| **Validate by** | Checklist §E plus malformed, oversized, cross-vendor, and scanner-positive fixture tests |
| **Reopen when** | Accepted formats expand beyond PDF or enterprise policy mandates a different quarantine/scanning flow |

### A-DATA-07 — Twenty-four hours limits signed access, not retention

| Field | Value |
|-------|-------|
| **Statement** | Interpret the “24-hour rolling link” note as the hard maximum lifetime for a vendor-authorized, GET-only Spaces presigned URL. Default expiry is one hour. Object retention remains a separate unresolved policy and is never shortened or extended implicitly by URL expiry. |
| **Confidence** | Medium until Dana confirms whether the note meant URL expiry, object retention, or both |
| **Impact if wrong** | If 24 hours meant object deletion, contracts may be retained too long; if it meant only access, deleting at 24 hours could violate business or legal needs. |
| **Owner** | Dana + Security/Legal |
| **Validate by** | Checklist §E retention answer and presigned-access review |
| **Reopen when** | Customer retention, legal hold, revocation, or download-window requirements change |

---

## Workload and reliability

### A-WORK-01 — Uploads are asynchronous

| Field | Value |
|-------|--------|
| **Statement** | The API accepts a file, stores it, creates a job id, and returns quickly. Extraction (20s–4m) runs in workers. This matches App Platform HTTP timeout realities (~100s) — see community/docs discussion of [request timeouts](https://www.digitalocean.com/community/questions/app-platform-request-timeout) and [App Platform limits](https://docs.digitalocean.com/products/app-platform/details/limits/). |
| **Confidence** | High |
| **Impact if wrong** | Synchronous “wait until extraction finishes” would reject App Platform web components. |
| **Owner** | Product + Engineering |
| **Validate by** | Confirm API contract with Dana |
| **Reopen when** | Enterprise requires synchronous end-to-end response |

### A-WORK-02 — Sizing is provisional until measured

| Field | Value |
|-------|--------|
| **Statement** | Worker count and memory are provisional until documents/minute, documents/hour, PDF size distribution, and simultaneous jobs are known. “Thousands of contracts” alone does not size the platform. |
| **Confidence** | High |
| **Impact if wrong** | Migration week may need temporary scale-up of worker `instance_count`. |
| **Owner** | FDE + Dana |
| **Validate by** | Checklist §A answers + load test |
| **Reopen when** | Measured peak exceeds planned concurrency |

### A-WORK-03 — Failure simulation is deterministic and non-production

| Field | Value |
|-------|--------|
| **Statement** | Timeout and failure behavior is injected through a seeded fault policy in unit tests and staging. Rates default to zero, and production startup rejects non-zero simulation configuration. Real network timeouts remain enforced independently. Locust (or an equivalent HTTP load tool) generates arrival load and soak traffic; it does not replace the seeded fault policy. Custom staging-only scripts inject operational faults Locust cannot create (worker kill, Valkey key removal, deploy-during-job). |
| **Confidence** | High |
| **Impact if wrong** | Unseeded tests become flaky; accidentally enabling artificial failures in production causes avoidable customer impact; using Locust alone leaves retry/DLQ and infra-failure evidence incomplete. |
| **Owner** | Engineering |
| **Validate by** | Deterministic unit tests, a production-configuration rejection test, Locust staging load/soak reports, and scripted failure timelines |
| **Reopen when** | A dedicated chaos platform replaces application-level simulation and operational scripts |

### A-WORK-04 — Inference limits are provisional exercise caps

| Field | Value |
|-------|-------|
| **Statement** | Until provider quota and load evidence are verified, cap the worker fleet at **10 concurrent inference calls**, use a **240-second hard inference timeout**, and interpret “three retries” literally as the initial attempt plus at most **three retries** before durable `dead_letter` and client-visible terminal failure. |
| **Confidence** | Medium — supplied as planning constraints, not verified provider limits |
| **Impact if wrong** | A lower provider quota causes throttling and queue growth; a higher safe quota may permit faster migration. A longer timeout can exceed worker drain/lease budgets. |
| **Owner** | FDE + Dana |
| **Validate by** | Provider/account quota check plus representative load, timeout, and DLQ tests |
| **Reopen when** | Provider quota, model latency, error rate, migration arrival rate, or budget materially changes |

### A-REL-01 — Conservative recovery envelope is a planning baseline only

| Field | Value |
|-------|--------|
| **Statement** | Until Dana chooses, plan around **RPO ≤15 minutes** and **RTO ≤60 minutes** for job metadata, with Spaces as durable PDF storage. This is **not** an agreed customer SLA. |
| **Confidence** | Medium |
| **Impact if wrong** | Near-zero RPO / 15-minute RTO raises cost and drill rigor; unresolved targets block cutover claims. |
| **Owner** | Dana / CTO |
| **Validate by** | Checklist §C + enterprise SLA text |
| **Reopen when** | SLA demands stricter targets |

---

## Delivery automation (replace SSH)

### A-DELIVERY-01 — Terraform owns infrastructure

| Field | Value |
|-------|--------|
| **Statement** | Reviewed Terraform creates/changes foundational DigitalOcean resources (managed data, Spaces, registry, project, and network). A separate versioned App Spec deployment job owns App Platform releases and arbitrary runtime secrets. Provider-generated database credentials may exist in protected Terraform state; application JSON does not. No snowflake SSH edits in production. |
| **Confidence** | High for the two-layer structure; Medium for final remote-state and CI secret products |
| **Impact if wrong** | Alternate IaC (Pulumi) is fine if equally reproducible. |
| **Owner** | FDE |
| **Validate by** | `terraform plan` against a clean account (later phase) |
| **Reopen when** | Org standard mandates a different IaC tool |

### A-DELIVERY-02 — CI builds immutable images; App Platform rolls forward/back

| Field | Value |
|-------|--------|
| **Statement** | CI builds, tests, scans, and publishes an immutable container image. Promotion triggers an App Platform rolling deployment with health checks and rollback — not `ssh` + `docker compose pull`. See [manage deployments](https://docs.digitalocean.com/products/app-platform/how-to/manage-deployments/) and [health checks](https://docs.digitalocean.com/products/app-platform/how-to/manage-health-checks/). |
| **Confidence** | High |
| **Impact if wrong** | If App Platform constraints bite, fall back to DOKS with the staffing cost accepted. |
| **Owner** | Engineering |
| **Validate by** | Staging rolling deploy demo (later phase) |
| **Reopen when** | Required runtime features are unsupported on App Platform |

### A-DELIVERY-03 — Worker drain covers worst-case jobs

| Field | Value |
|-------|--------|
| **Statement** | On deploy, workers stop taking new work and finish (or safely requeue) in-flight jobs. The provisional worst-case attempt budget is **510 seconds** (240s simulation + 240s inference + 30s durable completion), with a **570-second lease** and **600-second termination grace**. Default 120s is not enough. See [configure termination](https://docs.digitalocean.com/products/app-platform/how-to/configure-termination/). |
| **Confidence** | Medium-High |
| **Impact if wrong** | Jobs longer than grace period need checkpoint/requeue design. |
| **Owner** | Engineering |
| **Validate by** | Deploy-during-long-job test |
| **Reopen when** | Measured work cannot fit the 510-second attempt budget or the platform grace ceiling changes |

### A-DELIVERY-04 — Kubernetes is not the default Part 1 path

| Field | Value |
|-------|--------|
| **Statement** | Kubernetes manifests/Helm are **not** the default Part 1 delivery stack. They remain an alternative if Dana accepts staffing/ops trade-offs or measured requirements force DOKS (see ADR-001 reopen triggers). |
| **Confidence** | High (ensemble consensus) |
| **Impact if wrong** | Choosing DOKS now increases six-week delivery risk. |
| **Owner** | Dana / CTO / FDE |
| **Validate by** | ADR-001 acceptance |
| **Reopen when** | Triggers in [ADR-001](../decisions/ADR-001-part1-platform.md) fire |

### A-DELIVERY-05 — DOKS single-database-pod design is exercise-only

| Field | Value |
|-------|-------|
| **Statement** | Terraform-provisioned DOKS, one PostgreSQL StatefulSet pod, a CSI PVC, and seven days of snapshots may be demonstrated as an alternative exercise. They are not the Part 1 production database because one pod is not HA and CSI snapshots alone are not PostgreSQL-consistent backup/PITR. |
| **Confidence** | High |
| **Impact if wrong** | Treating the exercise topology as production silently accepts database downtime, shared failure domains, and unproven recovery. |
| **Owner** | CTO + named platform/DB owner |
| **Validate by** | Review the [DOKS exercise variant](../architecture/doks-exercise-variant.md), restore evidence, and explicit production topology decision |
| **Reopen when** | A platform/DB owner supplies and proves replication, WAL archival, restore, failover, upgrades, and on-call operations |

### A-DELIVERY-06 — Terraform composes environments from reusable modules

| Field | Value |
|-------|-------|
| **Statement** | Terraform has two layers: reusable core service modules and thin staging/production environment roots that promote the same reviewed commit/module version. Each environment has separate encrypted/locked state, credentials, plan, approval, and non-secret inputs. Managed database credentials may be state-resident provider attributes. Spaces/inference JSON is injected by protected App Spec deployment CI and never passed through Terraform. |
| **Confidence** | High for structure and security direction; Medium for final remote-state and CI secret products |
| **Impact if wrong** | Copied environment resources drift; a mega-module becomes hard to review; treating state as non-sensitive or passing application JSON through Terraform can expose credentials. |
| **Owner** | FDE + Security |
| **Validate by** | Module contract review, independent staging/production plans, state/plan secret scan, runtime injection and rotation test |
| **Reopen when** | Organization module registry, account isolation, or approved secret manager requires a different composition boundary |

---

## Quality assurance

### A-QUALITY-01 — Unit tests are a low-cost delivery gate

| Field | Value |
|-------|--------|
| **Statement** | Add automated unit tests for job-state transitions, retry limits, timeout handling, idempotency, and configuration before deployment. Unit tests run without DigitalOcean resources or network calls, so their cloud cost is **$0**; the cost is engineering time and a few CI minutes. |
| **Confidence** | High |
| **Impact if wrong** | Skipping tests makes queue acknowledgement, retry, and timeout regressions more likely—the same class of defects that can lose or duplicate jobs. Over-testing framework code would waste the one-day exercise budget, so focus on failure-prone business rules. |
| **Owner** | Engineering (tests); FDE (test plan); Dana (acceptance criteria) |
| **Validate by** | CI passes unit tests with ≥80% coverage on changed application logic; external clients are mocked |
| **Reopen when** | Integration behavior cannot be represented without managed services; add a separately gated integration test |

**Estimated implementation cost:** approximately **2–4 engineering hours** for
the simulation’s highest-risk paths, then seconds to a few minutes per CI run.
This is not a DigitalOcean infrastructure charge.

**Expected impact:** faster regression detection, safer refactoring, and
repeatable proof that retries do not duplicate results and failures do not
silently mark jobs complete. Unit tests do **not** replace load, failover,
restore, or live integration evidence.

---

## Budget assumptions

### A-BUDGET-01 — Part 1 vs Part 2 money are separate

| Field | Value |
|-------|--------|
| **Statement** | ~$400/month is current observed spend. Part 1 aims for a modest production envelope (roughly ~1–2× today if risks above are funded — exact ceiling TBD with Dana), **not** an unexplained 10×. The **$2,500/month** cap is for Part 2 self-hosted inference six months later and must not silently fund Part 1 overbuild. |
| **Confidence** | Medium |
| **Impact if wrong** | Wrong ceiling changes HA SKUs and worker counts. |
| **Owner** | Dana / CTO |
| **Validate by** | Checklist §D |
| **Reopen when** | Hard ceiling is stated in writing |

---

## Confidence summary

| Area | Level | Notes |
|------|-------|-------|
| Prefer App Platform + managed data for Part 1 | High | Ensemble B consensus |
| Exact monthly dollar figure | Medium | Needs Dana ceiling + measured load |
| Part 2 full-response &lt;2s @ 400 concurrent @ $2,500 | Low | Likely infeasible; model both interpretations |
| Root cause of 40 lost jobs | Unknown | Forensic checklist required |
