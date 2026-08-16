<!-- SPDX-License-Identifier: MIT -->

# Reconciliation and dead letters

PostgreSQL is authoritative. Valkey contains wake items only.

1. Check queue lag, reconciliation logs, expired leases, and PostgreSQL jobs in
   `accepted`, `retry`, or `dead_letter`.
2. Confirm the worker fleet and private PostgreSQL/Valkey connections are
   healthy before replaying anything.
3. Let reconciliation enqueue missing `accepted`/`retry` job ids once. Never
   create a job from queue contents.
4. Inspect a dead-letter job's attempts and failure reason. The limit is one
   initial attempt plus three retries.
5. Requeue only after the cause is fixed and an operator records approval;
   preserve attempt history and idempotency.

Escalate duplicate inference, cross-vendor access, unexplained ledger gaps, or
repeated dead letters. Never delete PostgreSQL rows to clear an alert.
