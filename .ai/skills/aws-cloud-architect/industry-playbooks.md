<!-- SPDX-License-Identifier: MIT -->

# AWS Industry Playbooks (Regulated Domains)

Domain-specific constraints, reference patterns, and AWS service mappings drawn
from 20+ years building regulated workloads. Load when the workload falls under
one of these regimes. The compliance regime drives account topology, region
choice, encryption, and logging — decide it in Step 1 of the operating model.

## Fintech / payments / banking

**Regime**: PCI DSS, SOC 2, SOX, PSD2/Open Banking, regional banking rules;
strong auditability and data residency.

- **Isolation**: dedicated account(s) for the cardholder data environment (CDE);
  SCPs restrict regions to in-scope only. Keep the CDE small to shrink PCI scope.
- **Data**: tokenize/vault PANs (never store raw where avoidable); KMS CMKs with
  per-environment keys; Aurora with encryption + audit logging; immutable WORM
  evidence in S3 Object Lock.
- **Patterns**: idempotent payment APIs (idempotency keys in DynamoDB),
  exactly-once-ish processing via SQS FIFO + dedup, event sourcing/ledger for
  auditable balances, strong reconciliation jobs.
- **Controls**: WAF + Shield Advanced on public edges, fraud signals via
  EventBridge, full CloudTrail data events on sensitive buckets/tables.
- **Resilience**: multi-AZ mandatory; multi-region active-passive for tier-1
  ledgers with tested RTO; chaos/game days for failover.

## Healthcare / life sciences

**Regime**: HIPAA/HITECH, HITRUST, GxP/21 CFR Part 11, GDPR for EU patients.

- **BAA**: use only HIPAA-eligible services; sign the AWS BAA; confirm eligibility
  before selecting any service for PHI.
- **PHI handling**: encrypt at rest (KMS CMK) and in transit; de-identify
  (Safe Harbor / Expert Determination) for analytics; segregate PHI from
  application telemetry.
- **Patterns**: HealthLake / FHIR data stores for clinical data; Glue + Lake
  Formation for governed analytics with row/column-level security; audit every
  PHI access (CloudTrail data events + application audit log).
- **GxP**: validated/qualified environments, change control, immutable audit
  trails, e-signature integrity for Part 11.
- **Residency**: keep PHI in-region; restrict cross-region replication to
  compliant regions only via SCP.

## Automotive

**Regime**: ISO 26262 (functional safety) toolchain integrity, ASPICE,
TISAX/ENX for data exchange, UNECE WP.29 (cybersecurity/OTA), GDPR for connected
vehicle data.

- **Connected vehicle / telemetry**: AWS IoT Core + IoT FleetWise for vehicle
  signal ingestion; Kinesis/MSK for high-volume streams; Timestream/S3 for
  time-series at scale; partition and tier aggressively for cost.
- **OTA & software-defined vehicle**: signed artifacts (code signing + KMS),
  staged rollout, rollback, and tamper-evident provenance for WP.29.
- **Toolchain integrity (ISO 26262)**: reproducible, versioned build/test
  pipelines; immutable artifact storage; traceability from requirement → test →
  binary. Treat the toolchain as a qualified asset.
- **Data exchange**: TISAX-aligned controls for sharing CAD/simulation data with
  suppliers; scoped cross-account access, no broad public sharing.

## Semiconductor / EDA / hardware

**Regime**: ITAR/EAR export control on design IP, trade-secret protection,
supplier/foundry data segregation.

- **EDA HPC**: EC2 (compute-optimized + high-memory, Graviton where the tool
  supports it) with Spot for fault-tolerant batch; FSx for Lustre as scratch;
  AWS Batch / Parallel Computing Service for job orchestration; license-server
  proximity and floating-license accounting.
- **Export control (ITAR/EAR)**: restrict to compliant regions (e.g. dedicated
  GovCloud-style boundary where required); SCPs deny non-approved regions;
  encrypt IP with CMKs the foundry/partner cannot access; tight egress controls.
- **IP segregation**: account-per-program or per-customer; no shared KMS keys
  across IP boundaries; Access Analyzer to prove no external exposure of design
  data; immutable audit of who touched which netlist/mask data.
- **Cost**: Spot + checkpointing for long EDA runs; storage lifecycle for the
  huge intermediate datasets; tag by project/tape-out for showback.

## Cross-domain checklist

- [ ] Compliance regime named and mapped to account topology + region set
- [ ] Data classified; residency enforced via SCP, not convention
- [ ] CMK strategy isolates tenants/programs/IP boundaries
- [ ] Service eligibility confirmed for the regime (BAA / in-scope / export)
- [ ] Immutable, centralized audit logging with the right retention
- [ ] RPO/RTO defined and the failover path tested
- [ ] Cost guardrails and per-program showback tagging in place
