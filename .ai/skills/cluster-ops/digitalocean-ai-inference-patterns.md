<!-- SPDX-License-Identifier: MIT -->
# DigitalOcean AI & Inference — Decision, Production, and Operations Patterns

Use this guide for DigitalOcean designs and any AI inference/serving decision.
Verify current regional SKU, quota, GPU, and managed-service capabilities against
live provider documentation before committing: availability and product limits
change faster than this reference.

## 1. Intake under ambiguous requirements

Ask only when the answer would materially change **cost, security, data loss,
availability, provider fit, or an irreversible architecture choice**. Otherwise,
proceed with safe defaults and show the assumption log.

### Essential questions

1. **Workload:** online API, asynchronous/batch, fine-tuning, or training?
2. **Model:** architecture/version, parameter count, precision/quantization,
   context and output lengths, framework/runtime, and model/data license?
3. **Demand:** requests or jobs per second, concurrent requests, burst factor,
   batch size, payload size, and growth horizon?
4. **Objectives:** p50/p95/p99 latency, time to first token (TTFT), inter-token
   latency, throughput, availability, recovery time (RTO), and data loss (RPO)?
5. **Data/security:** data locality, retention, tenant isolation, compliance,
   internet exposure, and secrets/key-management requirements?
6. **Economics/operations:** monthly ceiling, utilization pattern, deadline,
   environments, on-call owner, team Kubernetes maturity, and portability need?

### Safe defaults and assumption log

When answers are unknown and the choice is reversible, default to:

- one region and one production environment; stateless service with external
  object storage; no multi-region or Kubernetes until justified;
- private networking, deny-by-default inbound firewall, managed TLS at the edge,
  least-privilege credentials, encrypted storage, and no secrets in images/Git;
- online SLO starting point of 99.9% monthly availability, with targets for p95
  and p99 explicitly marked **TBD—measure in load test** rather than invented;
- two replicas for a revenue-serving stateless CPU service; for scarce/expensive
  GPU capacity, one active replica is acceptable only with declared downtime
  risk and a tested restore/redeploy path;
- 30% steady-state compute/GPU memory headroom, bounded queues, request
  timeouts, idempotent retries with jitter, and immutable versioned artifacts;
- daily backup of persistent control/config data, object versioning where
  supported, and restore verification before production.

Record each assumption as:

`A# | assumption | evidence/why safe | impact if wrong | validation owner/date`

Label overall confidence **High** (measured inputs and confirmed capability),
**Medium** (some estimates; reversible design), or **Low** (provider fit,
capacity, security, or SLO depends on unknowns). Low-confidence material choices
must become pre-production validation gates.

## 2. DigitalOcean placement decision

Choose the simplest product that meets the measured requirement. Do not force a
DigitalOcean service—or DigitalOcean itself—to fit an unsuitable workload.

| Option | Choose when | Hard constraints / rejection reasons |
|---|---|---|
| **GPU Droplets / Paperspace GPU** | Single-node inference, development, rendering, or bounded fine-tuning needing a known GPU and direct host/container control | Confirm GPU model/HBM, quota, region, attachable storage, driver/runtime compatibility, provisioning time, and HA semantics. Do not assume a low-latency RDMA fabric or multi-node collective performance. |
| **CPU Droplets** | Small/quantized CPU-fit models, batch workers, gateways, queues, control planes, or steady services where VM ownership is acceptable | Operator owns patching, process supervision, rollout, backups, and autoscaling. Reject when the model or latency target requires GPU acceleration. |
| **DOKS** | Multiple services/teams, Kubernetes-native rollout, horizontal replicas, policy, or mixed online/worker workloads justify cluster overhead | Verify required GPU worker support, device plugin/operator, storage mode, autoscaling, and regional capacity. Kubernetes does not create GPU capacity or a training-grade fabric. Reject for a small MVP without K8s competence. |
| **App Platform** | Stateless CPU web/API or worker, fast MVP, managed build/deploy/TLS, and supported runtime limits fit | Confirm CPU/memory, request/timeout, storage, networking, scaling, and GPU limits. Keep model weights/state external. Reject when privileged drivers, host tuning, local persistence, specialized GPU, or topology control is required. |

### Hard exits and migration triggers

- **Exit DigitalOcean for multi-node training** unless the exact offering proves
  gang capacity, topology, GPUDirect/RDMA, collective bandwidth, placement, and
  checkpoint throughput in a representative benchmark. Use a provider with a
  documented training fabric/capacity reservation when tightly coupled
  all-reduce crosses one node.
- Migrate when an approved region cannot repeatedly provision required capacity;
  p99/TTFT SLO fails after software and vertical tuning; the model no longer fits
  with at least 15% peak HBM margin; HA/RTO/RPO needs exceed the product's
  failure-domain controls; compliance/data residency cannot be met; or 90-day
  forecasted spend is materially lower on an alternative after migration and
  staffing costs.
- Move App Platform → Droplets/DOKS for host/GPU/runtime control. Move a single
  Droplet → DOKS only when replicas, services, team boundaries, or deployment
  frequency repay Kubernetes complexity. Move DigitalOcean → specialized GPU
  cloud when fabric, reserved capacity, GPU choice, or multi-node scale is the
  bottleneck.

## 3. Inference architecture reasoning

### Workload and sizing inputs

- **Online:** optimize bounded p95/p99, TTFT, inter-token latency, admission
  control, and availability. Avoid unbounded queues that convert overload into
  timeouts.
- **Batch/asynchronous:** optimize tokens or items per second and cost/result;
  use a durable queue, retries/dead-letter handling, checkpointable workers, and
  larger dynamic batches. Publish completion state outside worker-local disk.
- Size from concurrent active sequences, input/output context distribution,
  weights at selected precision, KV cache per token/layer, runtime workspace,
  batch/concurrency overhead, and fragmentation—not parameter count alone.
  Benchmark the real model, tokenizer, context distribution, and runtime.
- Validate GPU architecture, HBM, driver, kernel, CUDA/ROCm, framework, serving
  runtime, quantization, and container compatibility as one pinned matrix.

### Serving runtime: select only for fit

- **vLLM or TGI:** default candidates for transformer/LLM continuous batching;
  choose only after feature, model, quantization, and hardware compatibility
  tests.
- **Triton:** mixed model frameworks, ensembles, and mature inference backends;
  its flexibility is unnecessary for a simple single-model service.
- **Ray Serve:** Python-native multi-stage/model graphs or distributed serving
  where Ray is already justified; not a substitute for a missing GPU fabric.
- **KServe:** Kubernetes-standard model lifecycle, traffic splitting, and
  multi-team governance; avoid adding it solely to deploy one endpoint.

### Parallelism, batching, and scaling

1. Prefer **one complete model per GPU/replica** and horizontal replicas when it
   fits: this isolates failures and scales concurrency.
2. Use **tensor parallelism** only when weights + peak KV/workspace cannot fit on
   one GPU or one GPU cannot meet latency. Keep TP within a high-bandwidth node
   when possible; cross-node TP requires measured low-latency fabric.
3. Use continuous/dynamic batching with bounded wait time. Separate latency and
   batch queues when their objectives conflict; cap queue depth and reject or
   degrade gracefully above admission limits.
4. **Vertical scale** first when model fit, memory bandwidth, or single-request
   latency is limiting. **Horizontal scale** when independent-request
   throughput/availability is limiting. Scale on queue delay/depth and active
   sequences in addition to GPU utilization; CPU-only signals lag demand.

## 4. Production reference patterns

### MVP: reversible and low-operations

- App Platform for a CPU-fit stateless API, or one CPU/GPU Droplet/Paperspace
  instance with a pinned container runtime and supervised process.
- Cloud firewall permits only edge/admin paths; private networking for internal
  dependencies; TLS terminates at managed ingress/load balancer where possible.
- Images live in DigitalOcean Container Registry (DOCR), pinned by digest and
  scanned. Model/data artifacts live in versioned Spaces; use a Volume only for
  declared persistent block-storage needs. Never treat local boot disk as the
  sole copy.
- Inject secrets at runtime from an approved secret store/environment mechanism;
  use scoped tokens and rotation. Expose liveness and readiness separately;
  readiness remains false until model load and a minimal inference probe pass.
- Provision network, firewall, compute, registry/storage, DNS, and alerts with
  IaC. Deploy immutable versions, retain the prior version, and document a
  one-command redeploy/rollback. Name an application owner and on-call/runbook
  owner even if they are the same person.

### Revenue-serving: explicit availability and recovery

- Load balancer/managed ingress with TLS, restricted origin firewall, private
  east-west paths, egress controls where available, tenant-aware auth and rate
  limits. Use at least two replicas across available failure domains when the
  chosen GPU/service supports it; otherwise disclose the single-capacity risk.
- DOCR digest promotion across environments; signed/scanned images and SBOM.
  Spaces holds versioned weights/data/backups; Volumes hold only state requiring
  block semantics. Define snapshot/backup frequency from RPO and test restore to
  a clean environment.
- Externalize durable queue/state. Apply startup, readiness, liveness, and
  dependency probes without making transient downstream failure cause restart
  loops. Warm capacity before routing production traffic.
- IaC plus reviewed promotion; canary or blue/green rollout on model **and**
  application version labels. Automatically halt/rollback on SLO or correctness
  regression. Keep schema/artifact changes backward compatible through rollback.
- Runbooks cover overload, GPU fault, corrupt/missing model, dependency outage,
  rollback, restore, capacity shortage, and provider escalation. Every alert has
  an owning team, severity, action, and escalation path.

## 5. Failure-mode analysis

Every production design must state **detect / mitigate / prevent** for applicable
modes:

| Failure mode | Detect | Mitigate | Prevent |
|---|---|---|---|
| Capacity/quota shortage | Provisioning failures, pending nodes, quota and spare-capacity alert | Hold warm capacity; shed/defer load; fail over to approved shape/region/provider | Preflight quota; reserve where possible; quarterly capacity drill and portable artifact |
| GPU OOM / ECC / XID / thermal | Runtime OOM, DCGM/AMD metrics, kernel/device events, thermal/ECC counters | Stop admission; restart worker; drain/replace device; lower batch/context/concurrency | Peak-memory load test; ≥15% HBM margin; bounded inputs; pinned compatibility; burn-in |
| Model load / cold start | Startup and readiness duration, load errors, first-request TTFT | Keep old replica serving; extend startup only; prefetch/warm; route after probe | Versioned nearby artifacts; image/cache strategy; minimum warm replicas for strict SLO |
| Disk/Volume failure or exhaustion | I/O errors, latency, SMART/provider events, capacity/inode alerts | Replace/reattach; rebuild from object storage/IaC; restore verified backup | No sole local copy; quotas/retention; snapshots/backups and restore drills |
| Registry/object store/network dependency | Pull/read failures, synthetic probes, DNS/TLS/error/latency metrics | Use cached image/model; retry with jitter/circuit breaker; pause rollout; serve last good | Digest pinning; local warm cache; least dependencies on request path; tested outage mode |
| Autoscaling instability | Replica oscillation, pending time, queue/SLO divergence | Freeze/minimum replicas; widen cooldown; cap scale rate; shed load | Scale on queue + service time; hysteresis; realistic startup and capacity limits |
| Bad model/application rollout | Quality canary, SLO/error delta by model/app version | Halt traffic; instant weighted rollback; quarantine artifact | Offline eval, shadow/canary, signed promotion, backward-compatible contracts |
| Observability gap | Missing/stale series, scrape gaps, no version labels, alert delivery test failure | Fail rollout gate; switch to provider/log fallback; increase safe headroom | Telemetry SLO, synthetic probes, dashboard/alert-as-code, periodic paging test |

## 6. Observability, SLOs, and production gates

Instrument by endpoint, tenant class (without sensitive identifiers), region,
hardware, model version, quantization, runtime, and application version:

- request p50/p95/p99, TTFT, inter-token latency, end-to-end and generation
  tokens/s, batch size, active sequences, queue time/depth, cancellations,
  timeouts, retries, and errors by cause;
- GPU utilization, HBM used/total, power/thermals, clocks/throttling, ECC and XID
  (or AMD equivalent), plus CPU, RAM, disk, network, container restarts, model
  load time, and replica availability;
- availability and latency SLOs with fast/slow **error-budget burn alerts**,
  symptom alerts for users, and capacity alerts tied to runbook actions.

Do not call a workload production-ready until every applicable check is binary:

- `[PASS/FAIL]` Representative load test meets declared p50/p95/p99, TTFT,
  inter-token latency, tokens/s, error, and queue targets at forecast peak.
- `[PASS/FAIL]` Soak test covers expected sustained peak and shows no memory,
  latency, thermal, handle, disk, or queue growth.
- `[PASS/FAIL]` Peak HBM and steady compute retain ≥15% and target 30% headroom;
  overload is bounded by admission control and tested shedding/degradation.
- `[PASS/FAIL]` New and previous model/app versions are observable; canary abort
  and rollback complete within RTO without incompatible state.
- `[PASS/FAIL]` Kill/restart, dependency outage, capacity denial, corrupt/missing
  artifact, and storage restore tests produce expected alerts and recovery.
- `[PASS/FAIL]` Firewall/TLS, least privilege, secret rotation, image/artifact
  integrity, backup restore, IaC recreation, and named runbook ownership pass.

Any `FAIL` blocks production unless a named risk owner accepts it with expiry,
blast radius, compensating control, and remediation date. A missing measurement
is `FAIL`, not “unknown.” Record the exact remediation and rerun evidence.

## 7. Cost, reliability, and complexity decision framework

Score viable options against: monthly baseline and peak cost, cost/useful result,
capacity confidence, SLO/RTO/RPO fit, security/compliance, operational toil,
team skill, lock-in/migration effort, and growth headroom. Cost includes idle
capacity, storage/egress, backups, observability, support, and engineering/on-call
time—not only compute.

Pragmatic defaults:

- **Prototype:** local/Paperspace or one Droplet; no HA; hard spend cap; immutable
  artifacts and enough IaC to reproduce it.
- **MVP:** App Platform for CPU-fit stateless work, otherwise one right-sized
  Droplet/GPU; managed edge/TLS, external artifacts, backups, basic alerts, and
  documented redeploy. Accept downtime explicitly.
- **Revenue-serving:** redundant replicas/failure domains where capability
  allows, load balancer, tested rollback/restore, SLO burn alerts, warm capacity,
  security controls, on-call ownership, and forecast-based capacity.
- **Scale/multi-team:** DOKS only when orchestration/governance benefits exceed
  cluster toil; specialized provider or hybrid placement when DigitalOcean
  capacity, GPU/fabric, compliance, or unit economics fails a gate.

The final answer must select **one recommended option**, reject each serious
alternative with a concrete reason, and include a short plain-language summary:
what to run, why it is the safest economical fit now, what can fail, and what
measured trigger causes migration.

## 8. Required deliverable

Keep the result concise and use this order:

1. **Plain-language summary** — recommendation, why now, principal risk.
2. **Assumptions & confidence** — assumption log, unknowns, confidence level,
   and which unknowns are blocking gates.
3. **Recommendation & rejected alternatives** — one choice; cost/reliability/
   complexity comparison and explicit rejection reasons.
4. **Architecture** — request/data paths, compute/runtime/parallelism, network/
   TLS/firewall, registry/storage/secrets, health, backup, IaC, and ownership.
5. **Trade-offs & cost envelope** — low/base/high monthly range with usage,
   price-date, and excluded-cost assumptions; cost per useful result if known.
6. **Failure modes** — detect / mitigate / prevent.
7. **Rollout & rollback** — validation, canary/blue-green, abort thresholds,
   previous-version and state compatibility, RTO/RPO.
8. **Observability & SLO** — metrics, targets, labels, alerts, headroom, and
   PASS/FAIL evidence for load, soak, rollback, failure, restore, and security.
9. **Exit/migration triggers** — measurable capacity, SLO, model-fit, compliance,
   reliability, cost, or complexity thresholds and destination class.
