<!-- SPDX-License-Identifier: MIT -->

# DigitalOcean + AI Infrastructure Playbook

Use this playbook with the [DevOps Automator skill](../SKILL.md). Prefer the
simplest managed design that meets the stated SLO, security, recovery, capacity,
and budget constraints.

## Intake and Decision Record

Capture:

- Workload and interfaces; SLO; budget/cost ceiling; baseline, peak, burst, and
  growth traffic; data and model size; GPU need and precision; compliance/data
  residency; team operational maturity; RTO/RPO; existing repository, CI,
  registry, DNS, cloud, network, storage, and observability inventory.
- Material unknowns, each assumption, confidence (`high`, `medium`, or `low`),
  evidence still needed, chosen reversible default, and the measurable trigger
  that reopens the decision.

Ask only questions whose answers change architecture, cost, risk, compliance, or
reversibility. If an answer is unavailable, isolate the uncertain component and
choose a conservative, reversible default. Verify current DigitalOcean region,
SKU, GPU, quota, feature, and price availability through authoritative sources
before promising it; otherwise label it `unverified`.

## Platform Decision Matrix

| Option | Choose when | Cost/reliability/operations | Avoid or migrate when |
|---|---|---|---|
| App Platform | Stateless web/API/worker workloads with standard build and scaling needs | Lowest operational load; managed deployment and TLS; accept platform constraints and potentially higher unit cost | Specialized networking/runtime, stateful service, GPU, or fine-grained orchestration is required |
| CPU Droplets | Stable CPU workloads, custom runtimes, or low-cost single-service deployments | Good price control; reliability and patching require explicit redundancy, image management, and automation | Team cannot own hosts, demand is highly elastic, or orchestration burden grows |
| GPU Droplets | Model fits available GPU memory and direct VM control is justified | Potentially simple single-model serving; expensive idle capacity and more driver/runtime/host operations | Required SKU/region/capacity is unavailable, elasticity is dominant, or multi-node orchestration is needed |
| DOKS | Multiple services/models need Kubernetes scheduling, rollout, autoscaling, or policy | Strong flexibility and managed control plane; highest cluster and team complexity | One or two simple services fit App Platform/Droplets or the team lacks Kubernetes maturity |
| Managed databases/caches | Production state needs backups, patching, replication, or failover | Higher service price, substantially lower operational and recovery risk | Unsupported engine/extension, residency, latency, or scale requirement is material |
| Spaces / Volumes | Spaces for object/model artifacts and backups; Volumes for mounted block storage | Spaces decouples durable artifacts from compute; Volumes suit zonal filesystem needs but constrain mobility | Multi-region guarantees, storage semantics, throughput, or lifecycle controls do not fit |
| Another provider/architecture | A mandatory region, accelerator, managed AI feature, compliance control, capacity, global footprint, or economics is not met | Accept migration/integration cost to satisfy a hard requirement | Do not force DigitalOcean merely for platform consistency |

Prefer managed database/cache/storage, App Platform for straightforward
stateless services, a small automated Droplet design for justified custom
control, and DOKS only when orchestration benefits exceed its operational cost.
Avoid single-node production designs unless the accepted SLO and recovery plan
explicitly permit them.

## Production Infrastructure Contract

Implement or explicitly mark `not applicable` with rationale:

- Versioned, reviewed Terraform/IaC with pinned providers/modules, remote
  protected state and locking where supported, drift detection, plan review,
  policy/security checks, and no secrets in state or output.
- VPC/private paths, default-deny cloud firewalls, narrowly scoped ingress and
  egress, least-privilege identities/tokens, separated environments and blast
  radius, and documented administrative access.
- Managed DNS and TLS issuance/renewal; private service connectivity where
  supported; an immutable, scanned image in a registry with digest-based
  promotion and provenance/SBOM.
- Secrets from a secret store or protected platform injection, with scoped
  access, auditability, rotation, and restart/reload behavior tested.
- Automated backups with retention and encryption, plus a restore test against
  the stated RPO/RTO. Treat replication as availability, not backup.
- Isolated staging, explicit promotion, health/liveness/readiness/startup checks,
  capacity-aware autoscaling, graceful shutdown and draining.
- Immutable rolling, blue/green, or canary rollout with a bounded timeout,
  measurable success criteria, automatic/manual rollback, and a retained known
  good image/config/model.
- Structured logs, metrics, traces, alerts, dashboards, SLOs, ownership,
  escalation, dependency inventory, and a tested runbook.

Estimate a cost envelope rather than a single number: baseline, expected, and
peak compute/GPU hours; database/cache; storage and snapshots; network egress;
registry/observability; backups; support; and contingency. State pricing date,
currency, assumptions, discounts excluded, and unverified provider details.

## AI Serving Design

### Workload and Serving Fit

- **Online inference:** optimize bounded end-to-end latency, TTFT, inter-token
  latency, concurrency, cancellation, and overload behavior. Use admission
  control, bounded queues, timeouts, backpressure, and autoscaling on useful
  demand signals.
- **Batch inference:** optimize throughput and cost with durable jobs, chunking,
  idempotency, checkpoints, retry/dead-letter policy, and resumable outputs.
- Select a serving runtime based on model framework/format, quantization,
  accelerator support, memory fit, dynamic/continuous batching, streaming,
  parallelism, observability, and team supportability. Benchmark the actual
  model; do not select by popularity alone.

Before deployment, validate accelerator architecture, GPU memory, host RAM,
disk, PCIe/topology where relevant, OS/kernel, driver, container runtime,
framework, serving runtime, and compiled-kernel compatibility. Pin a tested
compatibility set and use startup self-tests. Never assume a cloud GPU SKU or
region is currently obtainable.

Store immutable model artifacts in object storage or a model registry with
version, digest, provenance, license, evaluation/security status, retention,
access controls, and promotion metadata. Download atomically, verify checksum,
reserve disk, and keep a rollback version. Never bake sensitive or frequently
changing weights into a public image.

### Capacity and Scaling

- Measure weight, KV-cache, activation, runtime workspace, and fragmentation
  memory. Reserve safety headroom; a model merely loading is not proof it can
  serve peak concurrency.
- Increase batch size/continuous batching only while latency SLOs and memory
  limits hold. Bound request size, sequence length, batch tokens, queue depth,
  and concurrent model loads.
- Prefer independent replicas for throughput, availability, and simple
  horizontal scaling when a model fits one GPU. Use tensor parallelism only
  when the model does not fit, or benchmarks show a necessary latency gain;
  account for communication overhead and larger failure domains.
- Scale vertically for memory fit or single-request latency; scale horizontally
  for throughput and resilience. Include warm-up, model-load time, scarce GPU
  capacity, minimum warm replicas, scale-up rate, cooldown, and quota in the
  autoscaling design.
- Publish tested limits: requests/connections, input/output tokens or payload
  size, queue depth, concurrency, batch size/tokens, replicas, GPU memory,
  artifact/disk size, rate limits, and degradation/rejection behavior.

## Operational Failure Modes

Each runbook entry must identify owner, severity, signal, safe action, rollback,
and escalation.

| Failure | Detect | Mitigate | Prevent |
|---|---|---|---|
| GPU OOM / XID | OOM logs, XID/kernel events, restart rate, memory/ECC/health metrics | Stop admission, drain/restart or quarantine GPU, reduce batch/context/concurrency, fail over | Memory budgets/headroom, bounded inputs, soak tests, compatible pinned stack, GPU health checks |
| Capacity unavailable | Provisioning errors, pending nodes/pods, quota/capacity alarms | Retain warm capacity, use approved fallback SKU/region/provider, shed noncritical load | Capacity verification/reservation where offered, quota checks, fallback design and drills |
| Cold start / model load | Startup/readiness duration, download/load failures, TTFT spikes | Keep minimum warm replicas, extend startup-only timeout, prefetch/cache verified artifacts | Smaller/quantized model, staged warm-up, capacity-aware rollout, artifact locality |
| Disk full | Disk/inode and artifact-cache alerts, write errors | Pause rollout/jobs, safely prune cache/logs, expand or replace volume | Quotas, retention/lifecycle rules, log rotation, preflight space checks |
| Dependency, registry, or object storage failure | Dependency SLI, pull/download errors, synthetic checks | Serve degraded/cached path, retry with jitter, circuit-break, use pinned local known-good artifact | Multi-copy artifacts where justified, dependency SLOs, digest pinning, failure tests |
| Autoscaler thrash | Rapid replica/node oscillation, queue and latency instability | Freeze or bound scaling, restore safe minimum, shed load | Stabilization windows, rate limits, useful signals, tested min/max and cooldown |
| Bad deploy or model | Canary SLO/evaluation regression, errors, drift, health failure | Halt promotion and roll back image/config/model together | Immutable versioning, canary gates, compatibility/evaluation tests, known-good retention |
| Secret rotation failure | Authentication errors, expiry alerts, old-version use | Roll back/dual-publish credential if safe, reload/restart dependents, revoke compromised key | Overlap window, automated rotation, versioned references, rotation drills |
| Cost runaway | Budget/forecast anomaly, GPU idle, egress/storage/telemetry spike | Cap scale/jobs, stop noncritical capacity, reduce retention or route safely | Budgets/alerts, quotas and max replicas, TTL labels, unit-cost dashboards, owner review |

## AI Observability

Attach environment, service, endpoint, model name/version/digest, runtime version,
hardware/SKU, region, deployment, replica, and request class labels while
controlling cardinality and excluding prompts, tokens, credentials, and PII.

At minimum observe:

- End-to-end latency p50/p90/p95/p99, TTFT, inter-token latency, request and token
  throughput, input/output tokens, concurrency, batch size/tokens, queue
  depth/wait, timeout/cancel/reject/error rates, retries, and model-load time.
- GPU utilization, memory used/headroom, temperature/power/throttling, ECC/XID
  events, host CPU/RAM/disk/network, container restarts, and replica/node state.
- SLO compliance and fast/slow burn-rate alerts tied to actionable runbooks;
  cost per request/job/token and utilization for capacity/cost decisions.

## Binary Production-Readiness Gate

Record each item as `PASS`, `FAIL`, or `N/A` with evidence; `N/A` requires an
owner-approved rationale. Production-ready is `PASS` only when every applicable
item passes:

- IaC plan/reproducibility, drift policy, least privilege, network controls,
  DNS/TLS, secrets rotation, registry digest/provenance, and high-severity
  image/dependency/IaC security scans pass.
- Health/readiness/startup, immutable promotion, canary/rolling behavior, and
  image/config/model rollback tests pass.
- Representative load and peak/burst tests meet SLO; soak test shows no leak or
  degradation; tested capacity retains documented CPU/RAM/GPU/disk/queue
  headroom and limits reject/degrade safely.
- Dependency, capacity, process/node, and GPU failure tests behave as designed;
  autoscaling remains stable.
- Backup restore test meets RPO/RTO, staging promotion passes, observability and
  model/version labels are queryable, SLO burn alerts route to a named owner,
  and the runbook is usable.

For any `FAIL`: assign owner and severity, fix the issue, rerun the failed test
and affected regression gates, attach new evidence, and repeat until all
applicable gates pass or an authorized risk acceptance explicitly blocks
production-ready status.

## Required Handoff

Write artifacts to repository-conventional paths, defaulting to:

- `infra/**` or `terraform/**` for IaC; `.github/workflows/**` for CI/CD;
  `Dockerfile*` or `docker/**` for images; `k8s/**` or `helm/**` for
  orchestration; `scripts/**` for automation; `docs/operations/**` or
  `runbooks/**` for architecture, readiness evidence, and operating procedures.

Give a non-expert summary containing the recommendation, assumptions/confidence,
plain-language reason, alternatives rejected, architecture, trade-offs, failure
modes, cost envelope, rollout and rollback, runbook and owner, plus measurable
migration/scale triggers. Clearly separate verified facts from estimates and
unverified DigitalOcean availability or pricing.
