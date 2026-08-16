<!-- SPDX-License-Identifier: MIT -->

# Deploy rollback

1. Stop promotion if API health, queue lag, worker errors, or inference
   concurrency breaches its provisional fleet cap of 10.
2. In protected CI, select the last known-good immutable image digest and its
   matching versioned App Spec. Do not rebuild or edit secrets locally.
3. Preview the App Spec change, then deploy it to App Platform. Keep at least
   two API and two worker instances and worker termination grace up to 600s.
4. Verify `/healthz`, one staging upload/status flow, worker drain/requeue, and
   PostgreSQL/Valkey private connectivity.
5. Record image digests, deployment ids, timestamps, owner, and job impact.

Escalate if rollback misses the agreed objective, accepted jobs disappear from
PostgreSQL, or Spaces objects cannot be read. Valkey loss alone is recovered by
ledger reconciliation; do not restore Valkey as the source of truth.
