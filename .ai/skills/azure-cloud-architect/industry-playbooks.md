<!-- SPDX-License-Identifier: MIT -->

# Azure Industry Playbooks (Regulated Domains)

Domain-specific constraints, reference patterns, and Azure service mappings drawn
from 20+ years building regulated workloads. Load when the workload falls under
one of these regimes. The compliance regime drives the management-group/
subscription topology, region choice, CMK, and logging — decide it in Step 1.

## Fintech / payments / banking

**Regime**: PCI DSS, SOC 2, SOX, PSD2/Open Banking, regional banking rules.

- **Isolation**: dedicated subscription(s) for the cardholder data environment
  (CDE); Azure Policy restricts regions to in-scope; Private Endpoints only for
  CDE data services. Keep the CDE small to shrink PCI scope.
- **Data**: tokenize/vault PANs; CMK in Key Vault/Managed HSM per environment;
  Azure SQL with TDE + auditing; immutable WORM evidence via Blob immutability
  policies.
- **Patterns**: idempotent payment APIs (idempotency keys in Cosmos DB), ordered
  processing via Service Bus sessions, ledger/event sourcing for auditable
  balances, reconciliation jobs.
- **Controls**: Front Door + WAF + DDoS Protection on public edges; Defender for
  Cloud regulatory compliance (PCI) dashboard; diagnostic logs on sensitive
  stores.
- **Resilience**: zone-redundant by default; multi-region active-passive for
  tier-1 ledgers with tested RTO; DR drills.

## Healthcare / life sciences

**Regime**: HIPAA/HITECH, HITRUST, GxP/21 CFR Part 11, GDPR for EU patients.

- **BAA**: use in-scope services; the Microsoft HIPAA BAA is included in the
  online services terms — confirm the specific service is covered for PHI.
- **PHI handling**: CMK at rest + TLS in transit; de-identify for analytics;
  segregate PHI from application telemetry.
- **Patterns**: Azure Health Data Services (FHIR / DICOM) for clinical data;
  Microsoft Purview for data governance, classification, and lineage; audit every
  PHI access via diagnostic + activity logs.
- **GxP**: validated/qualified environments, change control, immutable audit
  trails, e-signature integrity for Part 11.
- **Residency**: pin PHI to compliant regions; restrict replication via Policy
  allowed-locations; consider data-residency / sovereign options.

## Automotive

**Regime**: ISO 26262 toolchain integrity, ASPICE, TISAX/ENX, UNECE WP.29
(cyber/OTA), GDPR for connected-vehicle data.

- **Connected vehicle / telemetry**: Event Hubs (+ Kafka surface) and Azure IoT
  for vehicle signal ingestion; Stream Analytics / Databricks for processing;
  Data Explorer (ADX) for time-series at scale; partition and tier for cost.
- **OTA & software-defined vehicle**: signed artifacts (code signing + Key
  Vault), staged rollout, rollback, tamper-evident provenance for WP.29.
- **Toolchain integrity (ISO 26262)**: reproducible, versioned Azure Pipelines;
  immutable Azure Artifacts / ACR; requirement → test → binary traceability.
  Treat the toolchain as a qualified asset.
- **Data exchange**: TISAX-aligned controls for sharing CAD/simulation data;
  scoped cross-subscription access via Private Link, no broad public sharing.

## Semiconductor / EDA / hardware

**Regime**: export control (ITAR/EAR) on design IP, trade-secret protection,
supplier/foundry segregation.

- **EDA HPC**: Azure CycleCloud / Batch with HBv-series + Spot VMs for
  fault-tolerant batch; Azure Managed Lustre / NetApp Files as scratch;
  InfiniBand-enabled SKUs for tightly-coupled jobs; floating-license accounting.
- **Export control**: restrict to approved regions via Policy allowed-locations
  (sovereign/government clouds where required); CMK the foundry/partner cannot
  access; tight egress (Azure Firewall) to prevent IP exfiltration.
- **IP segregation**: subscription-per-program or per-customer; no shared CMK
  across IP boundaries; Defender + Access Reviews to prove no external exposure;
  immutable audit of access to netlist/mask data.
- **Cost**: Spot + checkpointing for long EDA runs; storage lifecycle for large
  intermediates; tags by project/tape-out for showback.

## Cross-domain checklist

- [ ] Compliance regime named and mapped to MG/subscription topology + region set
- [ ] Data classified; residency enforced via Azure Policy, not convention
- [ ] CMK strategy isolates tenants/programs/IP boundaries
- [ ] Service coverage confirmed for the regime (BAA / in-scope / export)
- [ ] Private Endpoints + public access disabled for sensitive data services
- [ ] Centralized Log Analytics + immutable retention; Defender/Sentinel on
- [ ] RPO/RTO defined and the failover path tested
- [ ] Budgets + Cost Management alerts and per-program tag showback in place
