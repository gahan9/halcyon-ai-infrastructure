<!-- SPDX-License-Identifier: MIT -->
# Scaling Tiers — SMB → Enterprise → Exascale

Pick the tier from measured requirements, then use the archetype as a starting
point. Do not jump tiers without a measured bottleneck.

## Tier 0 — SMB / startup / single researcher (1–8 accelerators)

- **Home:** one node (workstation or cloud VM). DigitalOcean GPU Droplets,
  Lambda on-demand, AWS `g6`/`p5` single instance, GCP `a3` single VM.
- **Fabric:** none inter-node needed; rely on single-node NVLink/Infinity Fabric.
- **Scheduler:** none, plain Docker/Compose, or Ray for local parallelism.
- **Storage:** local NVMe + object bucket for datasets.
- **Priorities:** cost first (spot/on-demand), fast iteration, reproducible env
  (containers), zero ops burden.
- **Anti-pattern:** buying InfiniBand or standing up Slurm for 4 GPUs.

## Tier 1 — Team / growth (8–64 accelerators, 1–8 nodes)

- **Home:** Lambda 1-Click Clusters, AWS Capacity Blocks / small UltraCluster,
  GCP A3 cluster, Azure ND-series, CoreWeave.
- **Fabric:** managed InfiniBand (1-click), AWS **EFA**, or tuned **RoCEv2**.
- **Scheduler:** **Slurm** (if HPC/training culture) **or** Kubernetes + Kueue
  (if cloud-native/inference). Pick one; don't run both yet.
- **Storage:** managed parallel FS (FSx for Lustre, Filestore, WEKA cloud) +
  object tier.
- **Priorities:** get the fabric verified (`nccl-tests`), reproducibility,
  basic accounting, checkpoint to shared FS.

## Tier 2 — Enterprise / platform (64 – several thousand accelerators)

- **Home:** reserved cloud capacity, dedicated GPU cloud (CoreWeave, Lambda,
  TensorWave for AMD), or on-prem/colo.
- **Fabric:** **non-blocking rail-optimized fat-tree**, InfiniBand NDR (400G),
  one NIC per GPU on its own rail; ≤2:1 oversubscription only if justified.
- **Scheduler:** **Slurm** for training + **Kubernetes** for services, often
  unified via **SUNK**; Volcano/Kueue for gang batch; fair-share + partitions
  for multi-tenant.
- **Storage:** high-BW parallel FS (WEKA/VAST/Lustre/Spectrum Scale) sized to
  checkpoint bandwidth; tiered to object; GPUDirect Storage where it pays.
- **Reliability:** multi-level checkpointing, DCGM/amd-smi health gating,
  automated node drain/replace, straggler detection.
- **Governance:** quotas, RBAC/SSO, cost showback/chargeback, image signing.
- **Priorities:** utilization (the KPI), multi-tenant fairness, MTBF at scale,
  observability, $ per useful result.

## Tier 3 — Exascale / national-lab / frontier AI (10k – 100k+ accelerators)

- **Home:** HPE Cray EX (Frontier, El Capitan, LUMI, Aurora), Fujitsu (Fugaku),
  custom hyperscaler AI supercomputers.
- **Fabric:** **Slingshot-11** (dragonfly), **Tofu-D** (6D mesh/torus), or
  hyperscaler custom; co-designed with the topology-aware app.
- **Scheduler:** Slurm and/or **Flux**, PBS Pro; topology- and
  reservation-aware; hierarchical.
- **Reliability:** failure is continuous → **async multi-level checkpoint/
  restart** (SCR/VeloC-style), Young/Daly-optimal intervals, in-job node
  replacement, silent-data-corruption detection, RAS telemetry pipelines.
- **Algorithms:** communication-avoiding / -overlapping, mixed precision
  (fp8/bf16 with fp32 accumulation, fp64 only where numerics demand),
  hierarchical/2D-3D collectives.
- **Physical:** warm-water **liquid cooling**, power capping/scheduling, PUE and
  MW-scale power planning are first-class design inputs.
- **Priorities:** sustained (not peak) FLOP/s on the real science/AI workload,
  power efficiency (GF/W), resilience, and reproducibility across restarts.

## Cross-tier sizing heuristics

- **HBM:** `weights_bytes + optimizer_state + activations + KV` must fit across
  chosen parallelism; leave ~20% headroom.
- **Fabric BW target (training):** aim for inter-node BW ≥ intra-node collective
  demand so all-reduce isn't the wall; validate empirically.
- **Checkpoint window:** `parallel_FS_write_BW ≥ full_model_state / target_seconds`;
  target seconds ≪ MTBF.
- **Checkpoint interval:** `≈ √(2 · checkpoint_cost · MTBF)` (Young/Daly).
- **Utilization gate for owning hardware:** sustained utilization ≳ 60–70% over
  the amortization window, else rent.
