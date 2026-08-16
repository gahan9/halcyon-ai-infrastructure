<!-- SPDX-License-Identifier: MIT -->

# Trade-offs: Part 1 compute platform (ensemble)

**Audience:** Dana, CTO, FDE. Score three ways to run the API and workers for
the six-week migration. Data layer (managed Postgres + managed Valkey + Spaces)
is assumed for Options A and B; Option C puts databases inside Kubernetes.

---

## Options (plain language)

| Option | Plain language | Technical label |
|--------|----------------|-----------------|
| **A** | Use Kubernetes (DOKS) for the app, but let DigitalOcean run the database, queue, and file storage | DOKS + managed PostgreSQL + managed Valkey + Spaces |
| **B** | Let DigitalOcean’s App Platform run the API and workers (no Kubernetes day-to-day), with managed database, queue, and files | App Platform + managed PostgreSQL + managed Valkey + Spaces |
| **C** | Run the app **and** Postgres/Valkey inside the Kubernetes cluster | DOKS + in-cluster PostgreSQL/Valkey |

---

## Ensemble scores

Reviewers and context windows from [Cursor docs](https://cursor.com/docs):

| Reviewer | Model | Context | A | B | C | Pick |
|----------|-------|---------|--:|--:|--:|------|
| Composer | Composer 2.5 | 200k default | 62 | **81** | 38 | B |
| GPT | GPT-5.6 Sol | 272k default / 1M max | 72 | **86** | 47 | B |
| Claude | Claude Opus 5 | 300k default / 1M max | — | — | — | **Unavailable (API limit mid-review)** |
| Substitute | Grok 4.6 | 256k default | 62 | **81** | 36 | B |

**Consensus for scaffolding:** **Option B**.

Shared scoring themes (weights varied slightly by reviewer; direction did not):

| Criterion | Why it mattered for Halcyon |
|-----------|------------------------------|
| Reliability / data loss | Already lost ~40 jobs after OOM on one box |
| Six-week delivery | Three engineers, no production K8s experience |
| Operational burden | No dedicated infra person |
| Monthly cost | ~$400 today; reject unexplained 10× |
| Security / scalability / portability / demo value | Secondary but scored |

The governing triad is **delivery time, operational certainty, and preferred
monthly bill**. Capacity is scalable only after measured queue, latency, memory,
provider-quota, and cost evidence shows where to add it.

---

## Executive proposal comparison

Costs are planning ranges, **not quotes**, and exclude Serverless Inference
tokens. “Uptime” describes the proposed topology and likely operational fit;
the customer SLA remains blocked until Dana chooses a recovery envelope.

| Decision factor | A — DOKS + managed data | B — App Platform + managed data | C — DOKS + in-cluster DBs |
|-----------------|-------------------------|----------------------------------|---------------------------|
| **Headline benefit** | Maximum orchestration control and strongest path to future Kubernetes/GPU node pools | Fastest production path with the least new operational burden | Lowest visible managed-service bill and maximum cluster control |
| **Estimated monthly platform cost** | **~$400–800** | **~$360–750** | **~$250–500 nominal**, excluding realistic database operations/incident labor |
| **Initial worker proposal** | ≥2 API pods + 2–4 worker pods across ≥2 nodes; autoscale later on queue metrics | ≥2 API instances + 2–4 fixed worker instances; scale temporarily for migration | Same app workers as A **plus** Postgres/Valkey pods, operators, and storage overhead |
| **Availability / uptime posture** | Can target 99.9% with HA control plane, multi-node app replicas, and managed data; team misconfiguration risk is material | Can target 99.9% at the API boundary with ≥2 instances and managed data; running jobs require tested drain/requeue | Weakest: app and databases share cluster/node/storage failure domains; 99.9% is not credible without significant DBA/K8s work |
| **Data-loss posture** | Strong: managed Postgres ledger + Spaces | Strong: managed Postgres ledger + Spaces | High risk until WAL archiving, replication, backups, and restore drills are proven |
| **Implementation complexity** | **High** — Terraform, DOKS, ingress, RBAC, network policy, probes, PDBs, HPA, Helm | **Low–Medium** — Terraform App resource/spec, health checks, managed-service wiring | **Very High** — everything in A plus database operators, persistent volumes, failover, and backup tooling |
| **Ongoing maintenance complexity** | **High** for three engineers: upgrades, add-ons, policies, autoscaling, cluster incidents | **Low–Medium**: application/runtime ownership; DigitalOcean operates the platform/data services | **Very High**: Kubernetes operations plus database administration and recovery |
| **Six-week delivery confidence** | 🟡 Medium-Low | 🟢 High | 🔴 Low |
| **Deploy improvement over SSH** | CI → image → Helm/Kubernetes rolling update | CI → image → App Platform rolling deployment and rollback | CI → image → Kubernetes, but stateful upgrade coordination is harder |
| **Blue/green cutover** | Keep one load balancer; switch stable Service/Ingress to green, drain old worker leases, then delete blue | Prefer App Platform rolling promotion + drain/requeue; no load-balancer replacement | App and stateful cutover are coupled; rollback is unsafe without expand/contract schema changes |
| **Unit-test cloud cost** | **$0**; same application unit suite for all options | **$0**; same application unit suite for all options | **$0**, but substantially more integration/failover testing is required |
| **Operational testing burden** | Medium-High: node loss, PDB, autoscaler, ingress, managed DB failover | Medium: worker kill, drain/requeue, App rollout, managed DB restore **and HA failover** | Very High: all of A plus in-cluster DB quorum, volume loss, WAL restore, operator upgrades |
| **Best fit when** | Dedicated platform owner exists or measured requirements exceed App Platform | Current Halcyon team, deadline, and workload | Rarely appropriate here; only with experienced K8s + DBA ownership |
| **Primary blocker** | No production Kubernetes owner | Traffic/RPO/budget inputs still missing—not a platform blocker | Unacceptable stateful operations and shared failure domain |

### Benefit, cost, and accountability

| Proposal | Customer benefit | Cost accepted | Decision owner | Recommendation |
|----------|------------------|---------------|----------------|----------------|
| **A** | More portability/control and future custom autoscaling | Kubernetes learning and on-call burden | CTO + named platform owner | 🟡 Defer until ownership exists |
| **B** | Durable jobs, safer deploys, and lower operational load inside six weeks | Managed-service fees and less low-level control | Dana + CTO, implemented by Engineering/FDE | 🟢 Approve after blockers are answered |
| **C** | Lower provider line items | Highest data-loss, recovery, and maintenance risk | CTO must explicitly accept risk; DBA + platform owner required | 🔴 Reject |

Pricing references (verify on purchase date):
[DOKS pricing](https://docs.digitalocean.com/products/kubernetes/details/pricing/),
[App Platform pricing](https://docs.digitalocean.com/products/app-platform/details/pricing/),
[PostgreSQL pricing](https://docs.digitalocean.com/products/databases/postgresql/details/pricing/),
[Valkey pricing](https://docs.digitalocean.com/products/databases/valkey/details/pricing/),
[Load balancer pricing](https://docs.digitalocean.com/products/networking/load-balancers/details/pricing/).

App Platform constraints to accept consciously:
[limits](https://docs.digitalocean.com/products/app-platform/details/limits/)
(workers: no request-based autoscaling; CPU autoscale on dedicated plans only;
local disk non-persistent; termination grace up to 600s).

### Managed PostgreSQL entry tier versus self-managed

DigitalOcean’s published pricing states that a single-node managed PostgreSQL
cluster with 1 GiB RAM starts at **$15/month**. DigitalOcean explicitly describes
that topology as **not highly available** and recommends it for preliminary
development/testing. Managed PostgreSQL generally provides automatic daily
backups and seven-day point-in-time recovery; verify those features on the exact
plan before purchase. The provider’s “automatic failover” wording for replacing
a single failed node is not equivalent to a ready matching standby.

| Database choice | Provider bill | What it removes | What remains / implementation decision |
|-----------------|---------------|-----------------|------------------------------------------|
| Managed PostgreSQL, 1 GiB shared single node | Starts ~$15/month | Host/engine patching, scheduled backup machinery, basic service operations | Not HA; use for staging or low-criticality exercise evidence, not enterprise production |
| Managed PostgreSQL HA | Starts with ~$30/month 2 GiB primary + at least one matching ~$30/month standby | Adds managed replication and standby failover; keeps backups/PITR and reduces DBA/on-call burden | Production baseline; minimum database node cost is therefore roughly $60/month before extras |
| One self-managed PostgreSQL pod/Droplet | May look “free” on already-paid compute | Nothing operational is transferred | Team owns upgrades, replication, WAL archive, restore, storage growth, corruption response, monitoring, failover, and on-call; rejected for Part 1 production |

The $15 plan materially improves staging economics, but it does not invalidate
the managed-versus-self-managed decision. For this three-engineer team, the
additional production HA database spend buys down a larger operational and
recovery risk than a single in-cluster pod can safely absorb. Downgrading
production to the $15 single node requires a named, expiring risk acceptance and
cannot claim the conservative recovery/availability envelope.

The visible premium from the ~$15 staging node to the ~$60 HA production pair
is roughly **$45/month**. At any loaded engineering cost above $45/hour, less
than one hour of monthly database toil erases that saving; self-managed
patching, backup verification, restore drills, monitoring, and incident response
are not credibly below that threshold. Record actual engineering hours and
incident cost rather than treating already-paid cluster capacity as free.

---

## Recommendation

**Choose B now.** Keep A as a documented reopen path. **Reject C** for
enterprise cutover.

Disagree with “keep Postgres inside the cluster” for this team size and
history: it recreates fate-sharing between application memory pressure and the
system of record.

A one-pod PostgreSQL StatefulSet with a PVC and seven days of CSI snapshots can
be an exercise, but it is not HA and snapshots alone are not a
PostgreSQL-consistent backup/PITR design. Likewise, Block Storage and Spaces are
not Valkey queue fallbacks; PostgreSQL reconciliation is. Defer the small CPU
Droplet 2–10-job worker idea for Part 1 because it adds host lifecycle and secret
operations without improving the selected managed-platform path.

Detailed alternative: [DOKS exercise variant](doks-exercise-variant.md).

Decision record: [ADR-001](../decisions/ADR-001-part1-platform.md).
