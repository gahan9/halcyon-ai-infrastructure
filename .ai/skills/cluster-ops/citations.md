<!-- SPDX-License-Identifier: MIT -->
# Citations & Where to Verify

Cite these when asserting a design fact. Vendor SKUs and Top500/Gordon Bell
records change; always confirm current specifics against the live source.

## ACM Gordon Bell Prize (reference designs)

- ACM Gordon Bell Prize — official record of winners/finalists (SC conference,
  ACM). Verify year, system, and reported performance here before quoting:
  https://awards.acm.org/bell
- Representative winners referenced in `reference-architectures.md`:
  - 2016 — 10M-core fully-implicit nonhydrostatic atmospheric dynamics solver
    (Sunway TaihuLight).
  - 2018 — "Exascale Deep Learning for Climate Analytics" (Summit); and the
    CoMet comparative-genomics winner (Summit).
  - 2020 — 100-million-atom molecular dynamics with ML (DeePMD) at ab initio
    accuracy (Summit).
  - 2021+ — quantum circuit simulation on new Sunway; COVID-19 Special Prize.
  - Confirm all years/claims at the ACM link above (do not quote from memory).

## Top500 / Green500 (system specs & rankings)

- https://top500.org — Frontier, Aurora, El Capitan, Fugaku, LUMI, Summit specs.
- https://green500.org — energy efficiency (GF/W) rankings.

## Interconnect & collectives

- InfiniBand / NDR — NVIDIA Networking (Mellanox) docs.
- NVLink / NVSwitch, NCCL, GPUDirect RDMA/Storage — NVIDIA developer docs.
- RCCL, ROCm, Infinity Fabric — AMD ROCm documentation.
- HPE **Slingshot** — HPE Cray EX / Slingshot technical briefs.
- Fujitsu **Tofu-D** / A64FX — Fujitsu/RIKEN Fugaku papers.
- `nccl-tests`, `rccl-tests`, OSU Micro-Benchmarks (`mvapich.cse.ohio-state.edu`).

## Schedulers & orchestration

- Slurm — SchedMD documentation (`slurm.schedmd.com`).
- Flux — `flux-framework.readthedocs.io`.
- Kubernetes: Kueue (`kueue.sigs.k8s.io`), Volcano (`volcano.sh`), JobSet,
  NVIDIA/AMD GPU Operator, KubeRay.
- CoreWeave **SUNK** — CoreWeave documentation.

## Resilience

- Young (1974) / Daly (2006) — optimal checkpoint interval formula.
- SCR (Scalable Checkpoint/Restart), VeloC — LLNL/ANL resilience libraries.

## Cloud providers

- AWS: EFA, UltraClusters, ParallelCluster, SageMaker HyperPod, FSx for Lustre,
  Capacity Blocks for ML — `docs.aws.amazon.com`.
- GCP: A3/A4, Cloud TPU, GKE, Cluster Toolkit, Parallelstore — `cloud.google.com`.
- Azure: ND-series, CycleCloud, Azure Managed Lustre — `learn.microsoft.com`.
- **Azure Red Hat OpenShift (ARO)** + OpenShift Virtualization — Red Hat/Azure docs;
  IBM hybrid modernization overview:
  https://www.ibm.com/new/product-blog/enterprise-ready-hybrid-cloud-why-cios-choose-red-hat-openshift-virtualization
- Lambda (`lambda.ai`), CoreWeave (`coreweave.com`), TensorWave
  (`tensorwave.com`), DigitalOcean/Paperspace (`digitalocean.com`).

## Hybrid OpenShift / platform engineering

- MeatyBytes — Top Design Patterns for the Modern Hybrid Cloud with OpenShift
  (Part 1): https://meatybytes.io/posts/openshift/architecture/ocp-patterns/patterns-pt-1/
- Red Hat OpenShift Service Mesh, GitOps, Advanced Cluster Management (RHACM),
  Serverless, Virtualization — `docs.redhat.com` / `access.redhat.com`.
- Kubernetes Patterns (Sidecar, Ambassador, etc.) — Red Hat / O'Reilly reference.

## Adapted community skills (attribution)

This skill's safe-operation and health-check patterns adapt ideas from:
- RC-up/cluster.skill (MIT) — shared-session monitoring, confirm-before-destroy.
- majiayu000/claude-skill-registry cluster-management — health-check / capacity
  workflow structure.
- Anthropic "Agent Skills" format and the Complete Guide to Building Skills.
