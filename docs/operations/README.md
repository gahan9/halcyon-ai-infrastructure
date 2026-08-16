<!-- SPDX-License-Identifier: MIT -->

# Operations runbooks

Option B runs API and worker components on DigitalOcean App Platform, with
managed PostgreSQL as the job ledger, managed Valkey as a disposable wake
queue, and private Spaces storage. Operators must use protected CI and
environment-scoped credentials; these documents do not authorize live changes.

- [Deploy rollback](deploy-rollback.md)
- [Reconciliation and DLQ](reconciliation-dlq.md)
- [Restore and failover](restore-failover.md)
- [Secret rotation](secret-rotation.md)
- [Inference budget](inference-budget.md)

Staging drills use `tests/load/locustfile.py` and `scripts/chaos/`. Production
readiness remains blocked until the live gates in `docs/evidence/README.md`
have captured, reviewed evidence.
