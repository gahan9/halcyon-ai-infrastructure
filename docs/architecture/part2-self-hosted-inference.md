<!-- SPDX-License-Identifier: MIT -->

# Part 2 — Self-hosted inference (design only)

**Status:** Design only — no implementation in this phase.  
**Horizon:** ~six months after Part 1, when Halcyon wants to leave Serverless
Inference for cost and/or data residency.

**Customer targets (as stated):**

| Requirement | Value |
|-------------|-------|
| Peak concurrent users | 400 |
| Average prompt tokens | 1,000 |
| Average output tokens | 300 |
| Target latency | &lt;2 seconds P95 |
| Availability | 99.9% |
| Monthly budget | Under $2,500 |
| Models under consideration | Llama 3.1 8B, Mistral Small, Qwen 14B |

---

## 1. Disambiguate before promising

Two interpretations of latency and concurrency must be modeled until Dana
clarifies (checklist §F):

| Scenario | Meaning | Feasibility under $2,500 + 99.9% |
|----------|---------|----------------------------------|
| **A — TTFT** | P95 time-to-first-token &lt;2s; completion may take longer while streaming | **Plausible** with 1–2 mid/large GPUs, right model, admission control, and overflow path |
| **B — Full completion** | P95 end-to-end for all 300 output tokens &lt;2s at 400 concurrent generations | **Likely FAIL** as a single point; implies enormous aggregate decode throughput and many GPUs |

Also clarify whether “400 concurrent users” means signed-in sessions or
**simultaneous in-flight generations**. The latter is the hard interpretation.

99.9% ≈ **43.8 minutes/month** error budget. A **single** GPU is one failure
domain — true HA needs N+1 or a failover path (e.g. Serverless Inference
overflow), which tensions the budget.

GPU list prices (on-demand, verify live):
[Droplet / GPU pricing](https://docs.digitalocean.com/products/droplets/details/pricing/).
Examples used in planning: MI300X ~$2.59/GPU/h; L40S / RTX 6000 ~$1.57/h;
H100 ~$4.41/h (one always-on H100 already exceeds $2,500/month). Powered-off
GPU Droplets can still bill while reserved — destroy when unused.

---

## 2. Model serving

| Choice | Guidance |
|--------|----------|
| Runtime | Prefer **vLLM** (or TGI) after compatibility test for the chosen weights/quantization — not by popularity alone |
| Topology | Prefer **one full replica per GPU** + horizontal replicas when the model fits |
| Tensor parallelism | Only if weights + KV + workspace do not fit one GPU |
| Batching | Continuous batching with **bounded** queue; reject or shed when full |
| Artifacts | Versioned weights in Spaces (or registry); digest-pin; never only on local disk |
| API shape | Keep OpenAI-compatible gateway in front so Part 1 workers swap base URL |

Do **not** require DOKS for Part 2 until benchmarks show multi-GPU scheduling
needs beyond a single GPU Droplet (or small fixed set).

---

## 3. GPU selection

| Candidate | When | Caution |
|-----------|------|---------|
| **Llama 3.1 8B** (quantized) | Default starting point for latency/cost | Validate extraction quality vs Serverless baseline |
| **Mistral Small** | If quality/latency wins on same hardware | Pin exact checkpoint + license |
| **Qwen 14B** | Only after 8B/Mistral miss quality **and** concurrency is far below worst-case 400 in-flight | Higher VRAM / lower concurrency |

| SKU direction | Role |
|---------------|------|
| **1× MI300X (192GB HBM)** | Comfortable HBM headroom for 8B-class + KV; ~$1,891/mo at $2.59×730h — fits budget for **one** GPU, not dual-GPU HA |
| **2× L40S or RTX 6000 (~48GB)** | Better for 99.9% with N+1; ~$2,292/mo at $1.57×730×2 — almost no margin for rest of platform |
| **H100 80GB** | Strong performance; always-on on-demand typically **over** $2,500 alone |

**Recommendation seed:** Benchmark quantized **Llama 3.1 8B** first on the
cheapest SKU that meets **Scenario A** with ≥15% HBM headroom. Treat Scenario B
as a **requirement change** unless benchmarks prove otherwise.

---

## 4. Scaling

- Vertical: get one replica meeting TTFT/memory before multiplying GPUs.
- Horizontal: add replicas for throughput and availability.
- Autoscale carefully: model load time, scarce GPU capacity, and minimum warm
  replicas dominate; scale on **queue wait + active sequences**, not CPU alone.
- Admission control: publish max concurrent generations; return 429/503 with
  retry guidance beyond the limit.
- Hybrid: self-host baseline + **Serverless Inference overflow/failover** to
  protect availability inside $2,500.

Part 1 App Platform cell stays; Part 2 is a **new serving cell**, not a rewrite.

---

## 5. Performance

Measure on representative prompts (1k in / 300 out):

- TTFT p50/p95/p99
- Inter-token latency
- End-to-end completion latency
- Tokens/s per GPU and per dollar
- Max concurrent generations before TTFT or HBM cliff
- Cold start / weight load time

Until measured, do **not** commit Scenario B.

Rough physics check: 300 output tokens at 150 tok/s ≈ 2.0s of decode **alone**
for a single stream — leaving little room for TTFT and scheduling at high
concurrency. This is why Scenario B is presumed failed pending evidence.

---

## 6. Observability

Labels: model name/version/digest, GPU SKU, replica, region, deployment id.
**Never** log raw contract text, prompts with PII, or API keys.

Minimum signals:

- Latency (TTFT, completion), throughput, queue depth, timeouts, rejects
- GPU utilization, HBM used/headroom, thermals, ECC/XID (or AMD equivalents)
- Availability SLO burn alerts (fast/slow)
- Cost per 1k tokens and GPU idle fraction

Tie alerts to runbooks: OOM, capacity pending, bad model rollout, prepaid/overflow
spend.

---

## 7. Cost

| Pattern | Ballpark | Fits $2,500? |
|---------|----------|--------------|
| 1× MI300X always-on | ~$1.9k GPU + leftover for API/DB | GPU yes; HA no |
| 2× L40S always-on | ~$2.3k GPU | Barely; almost no platform left |
| 1× H100 always-on | ~$3.2k+ | No |
| Stay Serverless | Usage-based prepaid | Often cheaper until residency forces self-host |

**Self-host only when** residency/compliance requires it **or** measured token
volume makes GPU unit economics clearly better **after** quality parity.

Clarify with Dana whether $2,500 is **GPU-only** or **entire platform**.

---

## 8. What we would need before signing Part 2

1. Checklist §F answers (concurrency + latency meaning)
2. Quality bar vs current Serverless model
3. Residency legal requirement statement
4. Benchmark evidence pack (load + soak + failover)
5. Explicit acceptance if Scenario B is dropped or SLO is renegotiated

---

## 9. Deliberate omissions (Part 2 design)

- Multi-node training fabrics / RDMA assumptions on DigitalOcean
- Starting on Qwen 14B
- Moving Part 1 onto DOKS solely to host GPUs
- Promising Scenario B under $2,500 without benchmarks
