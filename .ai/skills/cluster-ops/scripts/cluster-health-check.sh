#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# cluster-health-check.sh — read-only, multi-scheduler cluster triage snapshot.
#
# Detects the environment (Slurm / Kubernetes / LSF / PBS) and GPU vendor
# (NVIDIA / AMD), then prints a health summary. Performs NO write/destructive
# operations. Safe to run on any login/head node.
#
# Usage: ./cluster-health-check.sh
set -uo pipefail

hr() { printf '%s\n' "----------------------------------------------------------------"; }
have() { command -v "$1" >/dev/null 2>&1; }
section() { hr; printf '## %s\n' "$1"; hr; }

section "Host"
printf 'host: %s\n' "$(hostname -f 2>/dev/null || hostname)"
printf 'date: %s\n' "$(date -u +%FT%TZ)"
have uptime && uptime

section "GPU inventory & health"
if have nvidia-smi; then
  nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu,temperature.gpu,ecc.errors.uncorrected.aggregate.total \
    --format=csv,noheader 2>/dev/null || nvidia-smi
  echo "-- topology --"; nvidia-smi topo -m 2>/dev/null | head -n 20
elif have rocm-smi; then
  rocm-smi --showproductname --showuse --showmemuse --showtemp 2>/dev/null || rocm-smi
  have amd-smi && { echo "-- amd-smi --"; amd-smi monitor -u -m 2>/dev/null | head -n 20; }
  echo "-- topology --"; rocm-smi --showtopo 2>/dev/null | head -n 20
else
  echo "no GPU management tool (nvidia-smi/rocm-smi) found"
fi

section "Interconnect / fabric"
if have ibstat; then
  ibstat 2>/dev/null | grep -E 'State|Rate|Physical' | head -n 20
  have ibnetdiscover && echo "(run 'ibnetdiscover' as admin for full fabric map)"
else
  echo "no InfiniBand tools (ibstat) found; check EFA/RoCE via provider tooling"
fi

section "Scheduler state"
if have sinfo; then
  echo "== Slurm =="
  sinfo -o '%P %a %D %t %N' 2>/dev/null | head -n 30
  echo "-- drained/down nodes --"
  sinfo -R 2>/dev/null | head -n 20
  have squeue && { echo "-- queue depth --"; squeue -h 2>/dev/null | wc -l; }
elif have kubectl; then
  echo "== Kubernetes =="
  kubectl get nodes -o wide 2>/dev/null | head -n 30
  echo "-- GPU capacity (nvidia.com/gpu | amd.com/gpu) --"
  kubectl get nodes -o custom-columns='NODE:.metadata.name,NVIDIA:.status.allocatable.nvidia\.com/gpu,AMD:.status.allocatable.amd\.com/gpu' 2>/dev/null | head -n 30
  echo "-- not-ready nodes --"
  kubectl get nodes 2>/dev/null | grep -v ' Ready' | head -n 20
elif have bhosts; then
  echo "== LSF =="; bhosts 2>/dev/null | head -n 30; bqueues 2>/dev/null | head -n 20
elif have pbsnodes; then
  echo "== PBS =="; pbsnodes -aSj 2>/dev/null | head -n 30
else
  echo "no recognized scheduler CLI (sinfo/kubectl/bhosts/pbsnodes) found"
fi

section "Shared storage"
df -h 2>/dev/null | grep -Ei 'lustre|gpfs|weka|nfs|beegfs|vast|/scratch|/home' | head -n 20 \
  || df -h 2>/dev/null | head -n 10

section "Summary"
echo "Read-only snapshot complete. Investigate any: drained/not-ready nodes,"
echo "ECC/XID errors, links not in Active/LinkUp state, or full (>85%) scratch FS."
