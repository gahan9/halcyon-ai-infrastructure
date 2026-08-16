<!-- SPDX-License-Identifier: MIT -->
---
name: cluster-ops
description: >-
  State-of-the-art compute cluster design, provisioning, and operation across
  every scale — from a single-node SMB GPU box to enterprise multi-tenant
  clusters and national-lab exascale supercomputers. Covers accelerator/topology
  selection, interconnect fabrics (InfiniBand, NVLink/NVSwitch, Slingshot, RoCE,
  EFA, Tofu), scheduler choice (Slurm, Kubernetes+Volcano/Kueue, LSF, PBS, Ray,
  SUNK), parallel storage, reliability/checkpointing, observability, cost, and
  cloud provider patterns (AWS, GCP, Azure, Lambda, CoreWeave, TensorWave,
  DigitalOcean). Includes hybrid OpenShift platform engineering — federated
  identity, GitOps, RHACM multi-cluster governance, service mesh, serverless,
  and VM-to-container modernization (ARO/OpenShift Virtualization) with
  explicit trade-offs, off-track risk flags, and remedy plans. Grounds designs
  in ACM Gordon Bell Prize reference systems. Use when the user asks to design,
  size, provision, scale, benchmark, review, or troubleshoot a compute/HPC/AI/GPU
  cluster, choose a scheduler or fabric, plan capacity, compare cloud GPU
  offerings, or evaluate hybrid OpenShift/Kubernetes platform patterns.
license: MIT
metadata:
  version: 1.2.0
  authors: [gsaraiya]
  portability: Agent Skills open standard (Cursor, Claude Code, Copilot, Codex, Antigravity, Windsurf, Zed)
---

# cluster-ops — Cluster Design & Operations (SMB → Enterprise → Exascale)

Design, build, and run compute clusters that are **correct, scalable, secure,
and cost-defensible** at any scale. This skill encodes a principal-engineer
workflow plus reference designs distilled from ACM Gordon Bell Prize systems and
the operating practices of major GPU clouds.

## Core operating principle

**Size the cluster to the workload and the tier — never over-build, never
under-provision the bottleneck.** Every design decision must trace to a
measured or estimated requirement (model size, dataset throughput, comms
pattern, availability target, budget). When a requirement is unknown, ask for
it only when the answer materially changes cost/risk or an irreversible choice;
otherwise proceed with a safe default, assumption log, and confidence level.

## Decision workflow

Work through these gates in order. Do not skip ahead; each gate feeds the next.

```
Task Progress:
- [ ] 0. Resolve material ambiguity; log assumptions + confidence
- [ ] 1. Classify the workload
- [ ] 2. Pick the scale tier
- [ ] 3. Select accelerators + node shape
- [ ] 4. Design the interconnect fabric
- [ ] 5. Choose the scheduler / orchestration
- [ ] 6. Design storage + data path
- [ ] 7. Engineer reliability + observability
- [ ] 8. Secure + govern (multi-tenant, secrets, licensing)
- [ ] 9. Cost/reliability/complexity decision
- [ ] 10. Validate against a reference design
- [ ] 11. Apply DigitalOcean/inference gates when in scope
- [ ] 12. Apply hybrid OCP gates when in scope
```

### 0. Resolve material ambiguity

Collect workload, model, demand, SLO/RTO/RPO, data/security, budget, and operator
maturity inputs. Ask a question only if its answer can materially alter cost,
risk, provider fit, security, availability, or an irreversible decision.
Otherwise continue with documented safe defaults.

Every design with unknowns must include an assumption log (`assumption`,
`evidence/default`, `impact if wrong`, `owner/date to validate`) and a **High /
Medium / Low** confidence rating. Follow the full intake and safe-default rules
in `digitalocean-ai-inference-patterns.md`.

### 1. Classify the workload

Ask / determine the dominant pattern — it dictates everything downstream:

| Pattern | Signature | Fabric sensitivity |
|---------|-----------|--------------------|
| LLM/DL **training** | tight all-reduce/all-gather, sync SGD, long jobs | **Extreme** — needs non-blocking RDMA |
| LLM **inference/serving** | latency-bound, KV-cache, autoscale | Moderate (tensor-parallel = high) |
| Classical **HPC** (CFD, MD, weather) | MPI halo exchange, nearest-neighbor | High, topology-aware |
| **HTC** / embarrassingly parallel | independent tasks, sweeps | Low |
| **Data/ETL/analytics** | I/O-bound, shuffle | Storage + east-west network |

Key questions: model/problem size, precision (fp8/bf16/fp64), global batch,
collective pattern, job duration, SLA/availability, data volume & locality,
budget, regulatory constraints.

### 2. Pick the scale tier

See `scaling-tiers.md` for full decision tables. Summary:

| Tier | Accelerators | Fabric | Typical home | Scheduler |
|------|-------------|--------|--------------|-----------|
| **T0 SMB / startup** | 1–8 | PCIe / single-node NVLink | DigitalOcean, Lambda on-demand, 1 node | Docker / none / Ray |
| **T1 Team / growth** | 8–64 | RoCEv2 / EFA / 1-click IB | Lambda 1-Click, AWS Capacity Blocks | Slurm *or* K8s |
| **T2 Enterprise** | 64–thousands | Non-blocking InfiniBand (NDR), rail-optimized | Reserved cloud / colo / CoreWeave | Slurm + K8s (SUNK), Kueue |
| **T3 Exascale / national** | 10k–100k+ | Custom (Slingshot-11, Tofu-D), dragonfly | HPE Cray EX, Fugaku-class | Slurm/Flux + multi-level ckpt |

**Rule of thumb:** move up a tier only when the current tier's bottleneck is
measured, not anticipated. Most businesses live happily at T0–T2.

### 3. Select accelerators + node shape

- Match memory capacity/bandwidth to model footprint first (HBM GB per device,
  aggregate per node). A 70B bf16 model needs ~140 GB just for weights → plan
  device count and parallelism (TP/PP/DP/FSDP) accordingly.
- Prefer **fewer, fatter nodes** to cut inter-node comms for training; prefer
  **many thin nodes** for HTC/inference horizontal scale.
- Vendor-neutral: NVIDIA (H100/H200/GB200, NVLink/NVSwitch), AMD Instinct
  (MI300X/MI325X/MI355X, Infinity Fabric — huge HBM), Intel Gaudi, Google TPU,
  AWS Trainium/Inferentia. Choose on $/effective-FLOP, HBM, software maturity
  (CUDA vs ROCm vs XLA), and supply.
- CPU:GPU ratio, NUMA locality, PCIe gen/lanes, and NIC-per-GPU (rail design)
  are as important as the GPU SKU. See `provider-patterns.md`.

### 4. Design the interconnect fabric

This is the #1 differentiator of a good vs. bad training cluster.

- **Intra-node:** NVLink/NVSwitch (NVIDIA) or Infinity Fabric (AMD) for
  full-bandwidth GPU-GPU. Verify GPUDirect RDMA / P2P is enabled.
- **Inter-node:** InfiniBand NDR (400 Gb/s) or XDR for HPC/training; RoCEv2 for
  Ethernet shops (requires PFC/ECN tuning); AWS **EFA**; HPE **Slingshot-11**;
  Fujitsu **Tofu-D** (6D mesh/torus).
- **Topology:** rail-optimized **fat-tree** (non-blocking or ≤2:1
  oversubscription) is the default for AI. **Dragonfly(+)** for very large HPC.
  **Torus/mesh** where locality-aware apps dominate.
- One NIC **per GPU** on its own rail for large training; validate with
  `nccl-tests` / `rccl-tests` (bus bandwidth) and `ib_write_bw` / OSU
  micro-benchmarks before declaring the fabric healthy.

### 5. Choose the scheduler / orchestration

See `provider-patterns.md` → "Schedulers". Quick guide:

- **Slurm** — gang scheduling, topology-aware, accounting; default for HPC/
  training and national labs (often with **Flux** or **PBS Pro** at the top end).
- **Kubernetes** — for inference, mixed/elastic, cloud-native; add **Volcano**
  or **Kueue** + **JobSet** for gang/batch, **NVIDIA GPU Operator**, MIG,
  Karpenter, and a network operator for RDMA/RoCE.
- **SUNK (Slurm-on-Kubernetes)** — CoreWeave pattern; batch training under
  Slurm semantics on a K8s substrate. Good T2 compromise.
- **Ray** — Pythonic distributed for RL/serving/data; layers on K8s or Slurm.
- **LSF / PBS Pro / HTCondor** — established enterprise/HTC estates.

For AI serving, do not select an orchestrator or runtime by popularity. Route
through `digitalocean-ai-inference-patterns.md` to decide online vs. batch,
vLLM/TGI/Triton/Ray Serve/KServe fit, replica vs. tensor parallelism, bounded
batching/queues, and vertical vs. horizontal scaling from measured workload and
model-footprint inputs.

### 6. Design storage + data path

- **Parallel FS** for scratch/checkpoint: Lustre, IBM Spectrum Scale (GPFS),
  **WEKA**, **VAST**, BeeGFS. Object (S3/GCS/Azure Blob) for cold/data lake.
- Checkpoint I/O bandwidth must absorb a full-cluster write in ≪ job MTBF (see
  §7). Size FS bandwidth to `model_state_bytes / target_ckpt_seconds`.
- Cache/stage hot data local (NVMe) or via GPUDirect Storage. Avoid NFS for
  large-scale training scratch.

### 7. Engineer reliability + observability

At scale, **failure is the steady state.** Node MTBF × node count → cluster MTBF
drops fast; a 10k-node job may see failures hourly.

- **Multi-level / async checkpointing** (e.g., SCR-style: node-local → buddy →
  parallel FS). Checkpoint interval ≈ optimal per Young/Daly formula
  (`√(2·C·MTBF)`), where C = checkpoint cost.
- **Health checks** before and during jobs: GPU ECC, XID errors, NVLink/fabric
  link flaps, thermal, straggler detection; drain + cordon bad nodes.
- **Observability:** DCGM / amd-smi exporters → Prometheus/Grafana; Slurm/K8s
  accounting; per-job GPU util, fabric counters, power. Alert on silent data
  corruption and stragglers, not just hard downs.

### 8. Secure + govern

- Multi-tenant isolation (namespaces/partitions, network policy, MIG per-tenant),
  quotas and fair-share accounting, RBAC/SSO.
- **Secrets** via env/secret manager — never plaintext in manifests or images.
- **Licensing hygiene:** avoid GPL/AGPL/SSPL contamination in shipped tooling;
  record SPDX. Confirm dataset/model licenses.
- Supply-chain: signed images, pinned deps, minimal base images.

### 9. Cost model + build vs. rent

- Compare **on-demand vs. reserved/committed vs. spot vs. owned (colo)** on a
  3-year TCO including power, cooling, networking, staff, and utilization.
- Utilization is king: a 40%-utilized owned cluster is usually beaten by
  reserved cloud. Track **$ per useful token / per converged job**, not $/GPU-hr.
- SMB/bursty → cloud on-demand/spot. Steady high-util → reserved or owned.

### 10. Validate against a reference design

Before finalizing, check the design against the closest ACM Gordon Bell /
top-500 reference system in `reference-architectures.md` and confirm the
interconnect ratio, checkpoint strategy, and precision choices are consistent
with what has actually worked at that scale.

### 11. Apply DigitalOcean and inference gates

When **DigitalOcean, Paperspace, model serving, or inference** is in scope, run
the decision and production gates in `digitalocean-ai-inference-patterns.md`.
Compare GPU Droplets/Paperspace, CPU Droplets, DOKS, and App Platform where
applicable. State hard constraints and measurable exit/migration triggers.

Never force tightly coupled multi-node training onto DigitalOcean without
representative proof of gang capacity, topology, RDMA/GPUDirect collective
performance, and checkpoint throughput. If that proof is absent, recommend a
provider with a documented training fabric.

### 12. (Hybrid OCP) Apply platform pattern gates

When the design includes **OpenShift, ARO, or multi-cluster Kubernetes** (not
just bare Slurm/GPU fabric), run the gated decision flow in
`openshift-hybrid-design-patterns.md` **before** adopting service mesh,
serverless, or VM modernization waves.

**Do not pre-install all patterns.** Sequence: identity + GitOps → RHACM
governance → scoped mesh → serverless for fit workloads → VM modernization in
parallel waves.

For every pattern choice, explicitly state:
1. **Trade-off accepted** (what you gain vs. what you pay)
2. **Risk flag** to watch (symptom that the design is going off-track)
3. **Remedy/precaution** if the flag fires

GPU/HPC and Slurm estates may coexist with OCP — mesh and serverless apply to
the Kubernetes slice, not the batch fabric. Flag misfit workloads early.

## Reference material (progressive disclosure)

- `scaling-tiers.md` — SMB→enterprise→exascale decision tables and archetypes.
- `provider-patterns.md` — AWS, GCP, Azure, Lambda, CoreWeave, TensorWave,
  DigitalOcean, and Kubernetes best-practice building blocks + scheduler guide.
- `digitalocean-ai-inference-patterns.md` — ambiguous-requirements intake,
  DigitalOcean placement and production patterns, inference sizing/serving,
  failure modes, observability/SLO gates, and migration triggers.
- `reference-architectures.md` — ACM Gordon Bell Prize systems (Summit,
  Frontier, Fugaku, Sunway, El Capitan, LUMI, Aurora) and the design lesson each
  teaches.
- `citations.md` — papers, standards, and vendor docs to cite and where to verify.
- `openshift-hybrid-design-patterns.md` — hybrid OCP pattern catalog, off-track
  risk flags, remedy plans, and gated decision framework (IBM ARO + MeatyBytes).

## Required output contract and validation gate

Every recommendation must:

1. Select **one recommended option** and reject serious alternatives with
   reasons using cost, reliability, and operational complexity.
2. Start with a plain-language explanation for non-experts.
3. Include assumptions + confidence, architecture, trade-offs, failure modes
   (`detect / mitigate / prevent`), rollout/rollback, observability/SLO, a
   low/base/high cost envelope, and measurable migration triggers.
4. For production AI, report p50/p95/p99, TTFT, inter-token latency, tokens/s,
   queue time/depth, errors, GPU utilization/HBM/thermals/ECC/XID, model/version
   labels, SLO burn alerts, and capacity headroom where applicable.
5. Mark load, soak, rollback, dependency/failure, restore, security, and
   capacity-headroom checks **PASS or FAIL** with evidence. Missing evidence is
   `FAIL`; either remediate and rerun or record a named, expiring risk acceptance
   with blast radius and compensating control.

Use the concise deliverable template and binary remediation criteria in
`digitalocean-ai-inference-patterns.md`.

## Documentation & citation rules (apply to every answer and change)

1. **Doc-first, simple > complex.** Lead with the plain-language answer and,
   where it clarifies, an ASCII/[mermaid](https://mermaid.js.org/) diagram or a
   small table — not a wall of prose.
2. **Link, don't lecture.** Cite any non-obvious claim with an **inline
   hyperlink** rather than a long inline explanation.
3. **Back non-trivial claims with a credible source** — a journal/conference
   paper ([ACM](https://dl.acm.org/), [arXiv](https://arxiv.org/)), a standards
   body, a book, or a recognised vendor engineering blog. For cluster-scale
   assertions, prefer the ACM [Gordon Bell Prize](https://awards.acm.org/bell)
   record and the systems' official docs (see `citations.md`).
4. **Automate the sync.** After editing this skill, run
   `python scripts/sync-skill.py` so all agent homes stay identical; ship repo
   changes with the knowledge-network `tooling/ship.py` (sync → index → signed
   commit → push → PR). Don't hand-edit generated mirrors.

## Safe operation on real clusters

When this skill drives commands against a live cluster (submitting/killing jobs,
draining nodes, editing configs):

1. **Prefer a visible/audited session.** Run write operations where the user can
   see them (shared tmux, logged terminal) — no hidden side effects.
2. **Confirm before destructive actions** (`scancel`/`bkill`/`kubectl delete`,
   `rm` on shared FS, node drain/reboot). State exactly what, why, and the blast
   radius, then ask.
3. **Dry-run first** where the tool supports it (`--dry-run`, `sbatch --test-only`,
   `kubectl ... --dry-run=server`).
4. Never exfiltrate `confidential`/`secret` data or credentials into logs.

`scripts/cluster-health-check.sh` is a read-only, multi-scheduler triage helper —
run it (or read it) to snapshot cluster health before deeper work.

## Principal-engineer review lens (apply to any design you're given)

1. Is the core design correct for the workload class and tier?
2. What is the *bottleneck* (fabric, HBM, storage BW, power)? Is it the thing
   being spent on? If not — that's the finding.
3. Can it scale one tier up without a rewrite? If not, is that acceptable?
4. Reliability & security: checkpointing, health, isolation, secrets, licensing.
5. Cost: is $/useful-result defensible vs. the rent-vs-own alternative?
6. **DigitalOcean/inference (if applicable):** Did the design pass provider-fit,
   model-footprint, SLO, capacity, failure-mode, and production-readiness gates?
   Are hard exits and migration triggers explicit?
7. **Hybrid OCP (if applicable):** Are platform patterns sequenced correctly?
   Any risk flags from `openshift-hybrid-design-patterns.md` active? Is there a
   confirmed remedy if identity sprawl, mesh-before-inventory, or GitOps secret
   leakage is detected?

Classify feedback as 🔴 **Critical** (blocks correctness/scale/security) or
🟢 **Good to have** (non-breaking optimization). Appreciate solid designs
explicitly; point to the reference architecture or provider doc for anything you
assert.
