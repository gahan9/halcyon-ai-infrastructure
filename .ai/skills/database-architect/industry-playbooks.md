<!-- SPDX-License-Identifier: MIT -->

# Database Industry Playbooks, Certifications & Research

Regulated-domain data handling, plus the upskilling ladder and canonical sources
this skill distills. Load when the data is regulated, or for mentoring /
learning-path questions.

## Regulated-domain data handling

### Fintech / payments / banking (PCI DSS, SOX, PSD2)

- Never store raw PANs where avoidable — tokenize/vault; encrypt sensitive
  columns; keep the cardholder data store in a tightly scoped, audited boundary.
- Money is `numeric`/`decimal`, never float; model balances as an append-only
  **ledger** (event sourcing) so every change is auditable and reconcilable.
- Strong isolation (Serializable / explicit locks) for balance-affecting
  transactions; idempotency keys for payment operations.
- Immutable audit trail (who/what/when) with WORM retention for the required
  period; row-level security per tenant.

### Healthcare / life sciences (HIPAA, HITRUST, GxP/Part 11)

- Classify PHI explicitly; encrypt at rest with managed keys and in transit;
  apply column/row-level security and masking for non-clinical access.
- De-identify (Safe Harbor / Expert Determination) before analytics; segregate
  PHI from operational telemetry.
- Audit every PHI read and write; immutable trails for Part 11; validated schema
  change control in GxP environments.
- Pin data to compliant regions; control cross-border replication at the engine
  and platform level.

### Automotive (ISO 26262, TISAX, WP.29, GDPR)

- Connected-vehicle telemetry is high-volume time-series — partition by time +
  vehicle, downsample aggressively, tier old data; choose a TSDB or columnar
  store over a general OLTP engine.
- Maintain requirement → test → data lineage for safety traceability; treat the
  data pipeline's reproducibility as a qualified asset.
- Pseudonymize/anonymize personal driving data (GDPR); enforce consent-driven
  retention and deletion.

### Semiconductor / EDA (export control, trade secret)

- Design IP and mask/netlist data are crown jewels: encrypt with keys the
  partner/foundry cannot access; isolate per-program/per-customer schemas or
  instances; immutable access audit.
- Large EDA result sets need lifecycle/tiering and aggressive archival; keep hot
  metadata in a fast store and bulk artifacts in object storage.
- Enforce residency/export boundaries at the data layer, not just the network.

## Cross-domain data-security checklist

- [ ] Sensitive columns classified, encrypted, and masked for non-privileged use
- [ ] Least-privilege per-service DB users; no app-as-superuser
- [ ] Row/column-level security for multi-tenant or mixed-sensitivity data
- [ ] Immutable audit trail of data access with compliant retention
- [ ] Residency / cross-border replication controlled and documented
- [ ] Backups encrypted and restore-tested; key management owned and rotated

## Certifications & courses

| Track | Credential / course | For whom |
|-------|---------------------|----------|
| PostgreSQL | EDB PostgreSQL Associate/Professional | OSS relational depth |
| Cloud relational | AWS Database Specialty (retired → use cloud architect certs), GCP Pro Cloud Database Engineer, Azure DP-300 | Managed DB on a cloud |
| Distributed | MongoDB Associate/Professional Developer & DBA | Document modeling at scale |
| Analytics | Snowflake SnowPro, Databricks Data Engineer | Warehouse/lakehouse |
| Modeling | CDMP (DAMA) — data management/governance | Enterprise data architects |

- **Use The Index, Luke!** (free) — <https://use-the-index-luke.com/> — practical
  indexing across engines.
- **PostgreSQL official docs + "The Art of PostgreSQL"** — query/plan depth.
- Vendor query-tuning courses on Microsoft Learn, Google Cloud Skills Boost, and
  AWS Skill Builder for the managed engines.

## Foundational papers & books (read these first)

- Codd, **"A Relational Model of Data for Large Shared Data Banks"** (CACM 1970)
  — the foundation of relational databases.
- Gray & Reuter, **"Transaction Processing: Concepts and Techniques"** — the
  canonical reference on ACID, locking, and recovery.
- Stonebraker et al., **"The End of an Architectural Era (It's Time for a Complete
  Rewrite)"** (VLDB 2007) — why one-size-fits-all stalled; specialized engines.
- DeCandia et al., **"Dynamo"** (SOSP 2007) and Corbett et al., **"Spanner"**
  (OSDI 2012) — the two poles of the consistency/availability trade-off.
- Lakshman & Malik, **"Cassandra: A Decentralized Structured Storage System"**
  (2010) — wide-column, tunable consistency.
- **Kleppmann, "Designing Data-Intensive Applications"** — the modern synthesis;
  the single best book for this skill's worldview.
- **"Database Internals"** (Petrov) — storage engines, B-trees/LSM, replication.
