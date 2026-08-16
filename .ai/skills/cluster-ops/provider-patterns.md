<!-- SPDX-License-Identifier: MIT -->
# Provider & Orchestration Patterns

Vendor-neutral building blocks and the canonical way each major provider exposes
them. Always confirm current instance names/specs against live vendor docs
(`citations.md`) — SKUs change quarterly.

## AWS

- **Compute:** `p5`/`p5e` (H100/H200), `p4d/p4de` (A100), `trn1/trn2`
  (Trainium), `inf2` (Inferentia), `g6` (L4/L40S) for inference.
- **Fabric:** **EFA** (Elastic Fabric Adapter) with the **SRD** protocol +
  **GPUDirect RDMA**; **UltraClusters** provide non-blocking petabit-scale
  fabric; use **cluster placement groups**.
- **Orchestrate:** **SageMaker HyperPod** (managed resilient training, auto node
  replacement), **AWS ParallelCluster** (Slurm), **EKS** + Kubernetes, **AWS
  Batch**.
- **Storage:** **FSx for Lustre** (scratch/checkpoint), S3 (data lake),
  S3 ↔ FSx data repository association.
- **Capacity:** **Capacity Blocks for ML** (reserved GPU windows), Savings Plans.

## Google Cloud (GCP)

- **Compute:** **A3 / A3 Ultra / A4** (H100/H200/B200), **Cloud TPU** v5e/v5p/
  v6e (Trillium) **Pods**.
- **Fabric:** Jupiter datacenter network; **GPUDirect-TCPX/TCPXO** for GPU VMs;
  TPU Pods use dedicated ICI (inter-chip interconnect) in 2D/3D torus.
- **Orchestrate:** **GKE** (+ JobSet, Kueue), **Cluster Toolkit** (formerly HPC
  Toolkit) for Slurm, Vertex AI.
- **Storage:** **Filestore**, **Parallelstore** (DAOS-based), GCS, Cloud Storage
  FUSE, Hyperdisk.
- **Pattern:** TPU Pods for XLA/JAX at scale; A3 Ultra + GKE for GPU/PyTorch.

## Azure

- **Compute:** **ND H100 v5**, **ND MI300X v5** (AMD), NDm A100 v4, NC/NG series.
- **Fabric:** **NDR/HDR InfiniBand** (Mellanox) non-blocking on ND SKUs; NVLink
  intra-node.
- **Orchestrate:** **Azure CycleCloud** (Slurm/PBS/LSF), **AKS** + Kubernetes,
  **Azure Batch**, Azure ML.
- **Managed OpenShift:** **Azure Red Hat OpenShift (ARO)** — managed OCP with
  built-in RHEL licensing; **OpenShift Virtualization** for unified VM+container
  on one control plane (progressive modernization, not forced rewrite). Align
  identity with **Azure AD/OIDC** for federated RBAC across hybrid footprints.
  See `openshift-hybrid-design-patterns.md` for pattern sequencing and risk flags.
- **Storage:** **Azure Managed Lustre**, Azure NetApp Files, Blob (with NFS/
  BlobFuse), Azure HPC Cache.

## Lambda

- **Product:** on-demand + reserved H100/H200/GH200/B200; **1-Click Clusters**
  (turnkey InfiniBand multi-node); **Lambda Stack** (drivers/CUDA/frameworks
  preinstalled).
- **Pattern:** fastest path from 8 → 512 GPUs with real InfiniBand and minimal
  ops. Strong T1–T2 fit.

## CoreWeave

- **Product:** Kubernetes-native GPU cloud, non-blocking InfiniBand, bare-metal
  performance; **SUNK** (Slurm on Kubernetes); Tensorizer for fast model load;
  deep observability (fabric + GPU health).
- **Pattern:** T2 training at scale with K8s substrate + Slurm batch semantics.

## TensorWave

- **Product:** AMD-first cloud (**MI300X / MI325X / MI355X**), memory-optimized
  (large HBM per GPU), Slurm/Kubernetes.
- **Pattern:** memory-bound LLMs (long context, big models) where AMD HBM
  capacity and $/GB-HBM win; validate ROCm/RCCL software maturity for your stack.

## DigitalOcean (incl. Paperspace)

- **Product:** **GPU Droplets** (H100, AMD MI300X), Paperspace **Gradient**
  notebooks/deployments; simple, developer-friendly.
- **Pattern:** T0/SMB and inference/fine-tune; lowest ops overhead, not for
  large multi-node training.

## Kubernetes building blocks (any cloud or on-prem)

- **GPU enablement:** **NVIDIA GPU Operator** (drivers, DCGM, device plugin,
  MIG) or **AMD GPU Operator**; **Node Feature Discovery**.
- **Batch/gang:** **Kueue** (quota + gang), **Volcano** (gang, topology,
  fair-share), **JobSet** (multi-job LeaderWorkerSet), Kubeflow Training,
  **Ray** on K8s (KubeRay).
- **RDMA:** **Network Operator** + SR-IOV / RoCE / IB; multus for multi-NIC
  rails; verify GPUDirect RDMA end-to-end.
- **Autoscale:** Cluster Autoscaler or **Karpenter**; scale-to-zero for
  inference; topology-aware placement to keep gangs on one rail/spine.
- **Multi-tenant:** namespaces + ResourceQuota + NetworkPolicy + MIG slices;
  RBAC/SSO; cost via OpenCost/Kubecost.
- **Hybrid OCP platform (OpenShift/ARO):** Federated Identity (AD/Keycloak/Azure AD),
  **OpenShift GitOps** (Argo CD), **RHACM** (fleet governance), **OpenShift Service
  Mesh** (scoped mTLS/traffic policy), **OpenShift Serverless** (Knative — fit
  workloads only), **OpenShift Virtualization** (VM+container unified platform).
  Do not adopt all at once — use gated sequencing in `openshift-hybrid-design-patterns.md`.

## Schedulers — selection guide

| Scheduler | Best for | Notes |
|-----------|----------|-------|
| **Slurm** | HPC + large training | Gang, topology-aware, accounting; lab default |
| **Flux** | Exascale, hierarchical | Nested/co-scheduling at extreme scale |
| **PBS Pro / OpenPBS** | Enterprise HPC estates | Mature, commercial support |
| **LSF** | Legacy enterprise HPC | Common in finance/EDA |
| **Kubernetes (+Volcano/Kueue)** | Inference, elastic, cloud-native | Needs add-ons for gang batch |
| **SUNK** | K8s shops needing Slurm batch | CoreWeave pattern |
| **Ray** | RL, data, Python distributed | Layers on K8s/Slurm |
| **HTCondor** | High-throughput / grid | Independent tasks, opportunistic |

## Fabric verification (always do this before trusting a cluster)

- Collectives: `nccl-tests` (NVIDIA) / `rccl-tests` (AMD) — check bus bandwidth
  vs. theoretical; look for one slow rail dragging all-reduce.
- Point-to-point: `ib_write_bw`, `ib_read_lat`; OSU micro-benchmarks
  (`osu_allreduce`, `osu_bw`).
- Topology: `ibnetdiscover` / subnet manager health, `nvidia-smi topo -m`,
  `rocm-smi --showtopo`; confirm rail assignment and no link flaps.
