<!-- SPDX-License-Identifier: MIT -->

# PostgreSQL restore and failover

The staging single-node database can rehearse restore but cannot prove HA.
Production requires managed PostgreSQL with a matching standby and verified
backup/PITR for the selected RPO/RTO.

1. Declare the incident, stop writes if consistency is uncertain, and record
   the last known-good timestamp.
2. Use DigitalOcean's managed failover or restore workflow; never replace the
   ledger with Valkey or Spaces.
3. Bind App Platform to the recovered private endpoint through the protected
   deployment path. Do not expose credentials in commands or logs.
4. Verify database connectivity, schema version, accepted-job count, and a
   vendor-scoped upload/status flow.
5. Run reconciliation so durable `accepted`/`retry` jobs regain wake items.
6. Record achieved RPO/RTO, missing jobs, provider events, and evidence links.

Keep production cutover blocked until a production-sized failover and restore
meet the agreed targets.
