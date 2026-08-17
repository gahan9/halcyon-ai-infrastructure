<!-- SPDX-License-Identifier: MIT -->

# Data Patterns, Scaling & Consistency

Reference for the modeling patterns, scaling ladder, and consistency reasoning a
principal database architect reaches for. Load when designing for scale,
distributed data, or non-trivial integrity.

## Consistency & distributed-data fundamentals

- **ACID vs BASE**: pick ACID for money/inventory/identity; BASE (eventual) only
  where stale reads are acceptable and the write rate demands it.
- **CAP / PACELC**: under partition, choose consistency *or* availability; even
  without a partition there is a latency-vs-consistency trade-off (PACELC). State
  which side you chose and why.
- **Isolation levels**: know Read Committed (PostgreSQL default), Repeatable Read,
  and Serializable — and the anomalies each permits (dirty/non-repeatable/
  phantom reads, write skew). Use Serializable or explicit locking for invariants
  that span rows.
- **Idempotency & exactly-once**: real systems are at-least-once; achieve
  effectively-once with idempotency keys + dedup tables, not wishful thinking.

## Data-modeling patterns

| Pattern | Use when | Note |
|---------|----------|------|
| Normalization (3NF) | Default OLTP | Remove duplication; integrity by construction |
| Deliberate denormalization | Measured read hot path | Keep a consistency/refresh plan |
| Slowly Changing Dimensions (SCD type 2) | Need history/as-of queries | Versioned rows with validity ranges |
| Event sourcing / append-only ledger | Auditable state (balances, audit) | Rebuild state from immutable events |
| Outbox pattern | Reliable DB-to-broker publishing | Atomic write + async relay; avoids dual-write |
| CQRS | Read and write shapes diverge | Separate read models; accept eventual sync |
| Saga | Cross-service transactions | Orchestrated/choreographed compensations |
| Materialized views | Expensive recurring aggregates | Refresh strategy = correctness concern |
| Star/snowflake schema | Analytics/warehouse | Facts + dimensions for BI queries |

## Indexing depth

- **Composite index order** = equality columns first, then range, ordered by
  selectivity; the index can serve `ORDER BY` if it matches.
- **Covering indexes** (`INCLUDE`) avoid heap lookups for hot read paths.
- **Partial indexes** for skewed predicates (e.g. `WHERE status = 'active'`).
- **Expression/functional indexes** for computed predicates.
- **GIN/GiST** (PostgreSQL) for JSONB, arrays, full-text, and geo.
- Watch write amplification, bloat, and unused indexes — audit and prune.

## Scaling ladder (apply only the step the numbers justify)

1. **Tune** queries + indexes; fix N+1; right-size the instance. Most "scale"
   problems die here.
2. **Cache** hot reads (Redis) with an explicit invalidation strategy — a cache
   without invalidation is a latent correctness bug.
3. **Read replicas** for read-heavy load. Mind replication lag; route
   read-your-writes to the primary or use causal/session consistency.
4. **Vertical partitioning** (split wide/cold columns) and **archival** of cold
   data to cheaper storage/tiers.
5. **Horizontal partitioning** (range/list/hash) for very large tables — improves
   pruning, vacuum, and index size.
6. **Sharding** only when a single primary cannot hold the write volume. Choose a
   shard key that spreads load and matches the dominant query; accept cross-shard
   queries, distributed transactions, and rebalancing as real costs. Prefer a
   managed NewSQL engine (Spanner/Cockroach/Yugabyte) over hand-rolled sharding
   when global ACID is needed.

## Replication, HA & DR

- **Synchronous** replication for zero-RPO within a region (cost: write latency);
  **asynchronous** cross-region for DR (cost: potential data loss window).
- Define and rehearse **RPO** (max data loss) and **RTO** (max downtime); pick
  topology to meet them, then prove with failover and restore drills.
- Use automated failover (managed services / Patroni) and verify the application
  reconnects and respects read-your-writes after promotion.

## Migration safety (zero-downtime)

- **Expand → migrate/backfill → contract**: add new nullable columns / tables,
  dual-write or backfill in throttled batches, switch reads, then drop the old
  shape in a later deploy.
- Avoid blocking DDL on large tables (use online/concurrent index builds; tools
  like `pg_repack`, `gh-ost`, `pt-online-schema-change`).
- Test the migration on a production-sized copy; have a forward-fix and a
  rollback/recovery path. Never hand-edit an applied migration.

## Anti-patterns to flag in review

- String-concatenated SQL (injection); always parameterize.
- `SELECT *` on hot paths; unbounded result sets without pagination.
- Storing money as float; timestamps as strings; enums as free text.
- Premature sharding / NoSQL chosen to "avoid schemas".
- Caches and replicas without an invalidation / staleness story.
- Backups that have never been restored.
