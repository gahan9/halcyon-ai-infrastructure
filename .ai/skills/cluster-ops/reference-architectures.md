<!-- SPDX-License-Identifier: MIT -->
# Reference Architectures — ACM Gordon Bell Prize & Frontier Systems

Use these as validated "does-this-scale?" checkpoints. Each entry gives the
system, its defining architectural choice, and the **design lesson** to carry
into your own cluster. Always verify specifics against the ACM Gordon Bell Prize
record and the systems' official docs (`citations.md`) before quoting numbers.

## Systems and the lesson each teaches

### Frontier (OLCF, HPE Cray EX) — first exascale (>1 EF/s HPL)
- AMD EPYC + **MI250X**, 4 GCDs/node, HPE **Slingshot-11** dragonfly, Lustre
  (Orion).
- **Lesson:** exascale is a *networking + packaging* achievement as much as a
  compute one; dragonfly + high per-node injection BW and tight GPU-NIC coupling
  make the all-reduce tractable. Design the fabric first.

### El Capitan (LLNL, HPE Cray EX) — exascale APU
- AMD **MI300A** (APU: CPU+GPU+HBM unified), Slingshot-11.
- **Lesson:** **unified/shared memory** removes the host-device copy tax; when
  the workload is memory-movement-bound, converged APU beats discrete GPU+PCIe.

### Aurora (ALCF, HPE Cray EX) — Intel exascale
- Intel Xeon Max (HBM CPU) + **Data Center GPU Max (Ponte Vecchio)**,
  Slingshot-11.
- **Lesson:** HBM-on-CPU + many-tile GPUs; heterogeneity is manageable when the
  programming model (oneAPI/SYCL) and fabric are uniform.

### Fugaku (RIKEN, Fujitsu) — CPU-only, #1 on multiple lists
- **A64FX** Arm + SVE, HBM2 on-package, **Tofu-D** 6D mesh/torus, no discrete
  accelerators.
- **Lesson:** a balanced CPU with on-package HBM and a **torus** fabric can win
  broad real-application performance without GPUs; topology-aware placement is
  central. Balance beats peak FLOPs.

### Summit (OLCF, IBM) — pre-exascale GPU workhorse
- POWER9 + **V100**, **NVLink** CPU-GPU coherence, dual-rail EDR InfiniBand
  fat-tree, GPFS.
- **Lesson:** high-bandwidth **coherent CPU-GPU** links + fat-tree = the template
  most AI clusters still copy. 2018 Gordon Bell "Exascale Deep Learning for
  Climate Analytics" and the genomics winner ran here; 2020 winner (DeePMD,
  100M-atom MD with ML) also on Summit — mixed precision + ML surrogate is the
  recurring pattern.

### Sunway TaihuLight / OceanLight — many-core, custom
- SW26010 many-core, custom fabric.
- **Lesson:** the **2016 Gordon Bell winner** (10M-core fully-implicit
  nonhydrostatic atmospheric solver) showed **communication-avoiding, implicit
  solvers** unlock strong scaling to 10M cores; algorithm co-design > hardware
  alone. Later Sunway quantum-circuit-simulation work continued the theme.

### LUMI (EuroHPC, HPE Cray EX) — Europe's flagship
- AMD EPYC + **MI250X**, Slingshot-11, warm-water liquid cooled (heat reused).
- **Lesson:** **sustainability is architecture** — warm-water cooling + waste-
  heat reuse changes the power/TCO math at national scale.

## Recurring design lessons (apply everywhere)

1. **Fabric is the bottleneck at scale** — dragonfly/fat-tree/torus chosen to
   the collective pattern; per-node injection BW and GPU-NIC coupling decide
   whether all-reduce dominates.
2. **Mixed precision + algorithmic surrogates** (ML potentials, reduced/implicit
   solvers) are how Gordon Bell winners get order-of-magnitude speedups — not
   just more FLOPs.
3. **Communication-avoiding / -overlapping algorithms** are mandatory past ~10^4
   ranks.
4. **Coherent / unified memory** (NVLink C2C, MI300A APU, A64FX on-package HBM)
   removes copy overhead for memory-bound work.
5. **Resilience is designed in** — async multi-level checkpointing sized by the
   Young/Daly interval; assume continuous failure.
6. **Balance and sustained performance** (GF/W, real-app throughput) beat peak
   HPL. Fugaku is the canonical proof.

## How to use this file

For a proposed cluster: find the closest system by tier/workload, then confirm
your design's fabric topology, precision strategy, and checkpoint approach are
consistent with what worked there. If you deviate, state why.
