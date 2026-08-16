<!-- SPDX-License-Identifier: MIT -->

# GCP Industry Playbooks (Regulated Domains)

Domain-specific constraints, reference patterns, and Google Cloud service
mappings drawn from 20+ years building regulated workloads. Load when the
workload falls under one of these regimes. The compliance regime drives the
resource hierarchy, region choice, CMEK, and logging — decide it in Step 1.

## Fintech / payments / banking

**Regime**: PCI DSS, SOC 2, SOX, PSD2/Open Banking, regional banking rules.

- **Isolation**: dedicated folder/projects for the cardholder data environment
  (CDE); Org Policy restricts regions to in-scope only; VPC SC perimeter around
  CDE data services. Keep the CDE small to shrink PCI scope.
- **Data**: tokenize/vault PANs; CMEK with per-environment keys; Cloud SQL or
  Spanner with encryption + audit logging; WORM evidence via Cloud Storage
  retention lock.
- **Patterns**: idempotent payment APIs (idempotency keys in Firestore/Spanner),
  ordered/exactly-once-ish processing via Pub/Sub + Dataflow, ledger/event
  sourcing for auditable balances, reconciliation jobs.
- **Controls**: Cloud Armor (WAF/DDoS) + reCAPTCHA Enterprise on public edges;
  data access audit logs on sensitive datasets/buckets.
- **Resilience**: regional with multi-zone; Spanner multi-region for tier-1
  global ledgers with tested RTO; DR game days.

## Healthcare / life sciences

**Regime**: HIPAA/HITECH, HITRUST, GxP/21 CFR Part 11, GDPR for EU patients.

- **BAA**: use HIPAA-covered services only; execute the Google Cloud BAA; confirm
  coverage before selecting any service for PHI.
- **PHI handling**: CMEK at rest + TLS in transit; de-identify with Cloud DLP
  (Sensitive Data Protection) for analytics; segregate PHI from telemetry.
- **Patterns**: Cloud Healthcare API (FHIR/HL7v2/DICOM stores) for clinical data;
  BigQuery + DLP + column-level security and policy tags for governed analytics;
  audit every PHI access via data access logs.
- **GxP**: validated environments, change control, immutable audit trails,
  e-signature integrity for Part 11.
- **Residency**: pin PHI to compliant regions; restrict replication via Org
  Policy resource-location constraint.

## Automotive

**Regime**: ISO 26262 toolchain integrity, ASPICE, TISAX/ENX, UNECE WP.29
(cyber/OTA), GDPR for connected-vehicle data.

- **Connected vehicle / telemetry**: Pub/Sub for high-volume vehicle signals;
  Dataflow for stream processing; Bigtable/BigQuery for time-series at scale;
  partition and tier aggressively for cost.
- **OTA & software-defined vehicle**: signed artifacts (Binary Authorization +
  KMS), staged rollout, rollback, tamper-evident provenance (SLSA) for WP.29.
- **Toolchain integrity (ISO 26262)**: reproducible, versioned Cloud Build
  pipelines; immutable Artifact Registry; requirement → test → binary
  traceability. Treat the toolchain as a qualified asset.
- **Data exchange**: TISAX-aligned controls for sharing CAD/simulation data;
  scoped cross-project access via VPC SC, no broad public sharing.

## Semiconductor / EDA / hardware

**Regime**: export control (ITAR/EAR) on design IP, trade-secret protection,
supplier/foundry segregation.

- **EDA HPC**: Compute Engine (compute-/memory-optimized, with Cluster Toolkit /
  managed Slurm) + Spot VMs for fault-tolerant batch; Parallelstore/Filestore as
  scratch; Batch for orchestration; floating-license accounting and proximity.
- **Export control**: restrict to approved regions via Org Policy
  resource-location constraint; CMEK the foundry/partner cannot access; VPC SC
  perimeter + tight egress to prevent IP exfiltration.
- **IP segregation**: project-per-program or per-customer; no shared CMEK across
  IP boundaries; IAM Recommender + SCC to prove no external exposure; immutable
  audit of access to netlist/mask data.
- **Cost**: Spot + checkpointing for long EDA runs; storage lifecycle for large
  intermediates; labels by project/tape-out for showback.

## Cross-domain checklist

- [ ] Compliance regime named and mapped to hierarchy + region set
- [ ] Data classified; residency enforced via Org Policy, not convention
- [ ] CMEK strategy isolates tenants/programs/IP boundaries
- [ ] Service coverage confirmed for the regime (BAA / in-scope / export)
- [ ] VPC Service Controls perimeter around sensitive data services
- [ ] Immutable, centralized audit logging (incl. data access) with retention
- [ ] RPO/RTO defined and the failover path tested
- [ ] Budgets + BigQuery quotas and per-program label showback in place
