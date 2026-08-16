<!-- SPDX-License-Identifier: MIT -->

# Evidence pack (deferred)

This folder will hold proof that the Part 1 platform is ready for the largest
customer’s migration. Offline unit tests and static IaC/App Spec artifacts now
exist. **Live apply, deploy, load, chaos, restore, and production-readiness
claims remain blocked** until checklist approvals and spend authorization.

## Planned demonstrations

| Evidence | Pass criteria | Artifact to capture |
|----------|---------------|---------------------|
| Unit tests | Job transitions, idempotency, timeout/retry ceilings, acknowledgement ordering, and DLQ rules pass without network access; ≥80% coverage on changed app logic | CI test + coverage report |
| Clean-account bring-up | Terraform creates isolated foundations (network/project, managed Postgres/Valkey, private Spaces, registry); secure App Spec CI then creates/updates App Platform, attaches bindables, and injects scoped secrets | Redacted Terraform plan/apply + App Spec deployment logs |
| Terraform composition | Independent staging/production roots call the same pinned core module and produce isolated state/plan artifacts without copied resource logic | module contract test + redacted plans/state metadata |
| Runtime credential isolation | Terraform plan/state contain no application Spaces/inference JSON; provider-generated database credentials are confined to encrypted, locked, access-controlled state; malformed/wrong-environment JSON fails closed; API/worker receive only scoped credentials; audited App Spec rotation succeeds without logging/persisting plaintext | plan/state access review + secret scan + configuration/rotation test |
| Upload → job → result | Simulated contract returns structured status without blocking HTTP | curl / screenshot + job id |
| Vendor isolation | Vendor A cannot create, read, list, or infer Vendor B objects/jobs; vendor identity is server-derived | authorization test log + redacted audit event |
| Vendor tag / object metadata | Spaces object key prefix and metadata `vendor_id`/`job_id` match the PostgreSQL job row | Spaces head/metadata screenshot + DB row (redacted) |
| Upload security | Oversized, malformed, unsupported, and scanner-positive fixtures never reach the queue/inference path | test report + quarantine/rejection event |
| Inference timeout handling | Hung call fails within configured timeout; job retries then DLQ | logs + job attempt history |
| Inference concurrency cap | Runtime PostgreSQL semaphore keeps all old/new replicas at or below 10 in-flight calls; deployment also rejects a configured maximum above the cap | overlap/rolling test + in-flight/429 metrics |
| Three-retry ceiling | Initial attempt plus at most three retries transitions durably to `dead_letter`, and vendor-scoped status reports terminal failure | unit/integration test + job attempt history |
| Deterministic fault simulation | Fixed seed/outcome reproduces timeout and failure; production rejects non-zero simulation rates | unit/configuration test output |
| Locust load / soak | Staging Locust (or equivalent) meets agreed arrival/completion targets, p95 queue wait, and error rate without exceeding the inference concurrency cap or prepaid budget | Locust HTML/CSV report + queue and inference metrics |
| Custom failure drills | Staging-only scripts demonstrate worker kill, Valkey item loss, and deploy-during-job with recoverable job history | script log + job attempt timeline |
| Worker kill | Kill worker mid-job; job returns to `accepted`/`retry` from Postgres ledger | timeline |
| Queue-loss recovery | Removing a Valkey item leaves the PostgreSQL job intact and reconciliation re-enqueues it once | job history + queue/reconciliation metrics |
| Rolling deploy | API stays healthy during release; long job drained or requeued within grace ≤600s | deploy event + health |
| Postgres restore drill | Restore to point-in-time / backup within agreed RTO | restore runbook checklist |
| PostgreSQL HA failover | Production-sized primary loss promotes the matching standby, application reconnects, and accepted jobs remain recoverable within the availability/RTO target | provider event + application timeline + job reconciliation evidence |
| OOM isolation | Worker OOM does not take down API instances | metrics |
| Cost snapshot | Monthly estimate vs ceiling separates ~$15 managed PostgreSQL staging from ~$60+ managed HA production, records staging as additive, and compares self-managed engineering hours/incidents against the ~$45 visible monthly saving; inference prepaid balance monitored | spreadsheet + current DO pricing/billing and labor evidence |
| Presigned object access | Authorized vendor receives a GET-only private Spaces URL with one-hour default and ≤24-hour maximum; cross-vendor signing is denied and URLs are absent from logs | authorization test + redacted object metadata |

If ADR-001 reopens DOKS and funds the exercise variant, add evidence for node
drain, default-deny NetworkPolicy, PostgreSQL-aware backup plus new-PVC restore,
the explicitly weaker exercise RPO, stable-load-balancer blue/green routing,
blue-worker scale-to-zero/lease drain, and the runtime inference semaphore
during overlapping releases. These are not required to implement Option B and
do not authorize a DOKS deployment by themselves.

## Commands and artifact locations

These commands document collection paths; they have not been run here. Create
the ignored `artifacts/` directories before redirecting reports. Any command
that contacts DigitalOcean requires explicit approval and staging-only
credentials.

| Check | Command | Artifact |
|-------|---------|----------|
| Unit tests | `cd app && uv sync --all-extras && uv run pytest -x --cov=halcyon_sim --cov-report=term-missing --cov-report=xml:../artifacts/unit/coverage.xml --ignore=tests/integration` | `artifacts/unit/coverage.xml` |
| Terraform validate | `terraform -chdir=infra/terraform/environments/staging init -backend=false && terraform -chdir=infra/terraform/environments/staging validate -json > artifacts/terraform/staging-validate.json` | `artifacts/terraform/staging-validate.json`; apply remains gated |
| Docker build | `docker build --tag halcyon-sim:evidence app` | Local image `halcyon-sim:evidence` plus captured build log |
| Staging load | `LOAD_ENV=staging STAGING_API_BASE_URL=... STAGING_API_BEARER_TOKEN=... uvx --from locust locust -f tests/load/locustfile.py --headless --html artifacts/load/report.html --csv artifacts/load/results` | `artifacts/load/report.html`, `artifacts/load/results*.csv`; never use production credentials |
| Chaos dry runs | `APP_ID=... WORKER_COMPONENT=... bash scripts/chaos/worker_kill.sh --env=staging`; run the other scripts with their documented variables | Captured stdout under `artifacts/chaos/`; scripts only describe drills and do not mutate staging |
| App Spec | Review `deploy/app-spec.staging.yaml` / `deploy/app-spec.production.yaml` | Spec files only; CI deploy blocked without spend approval |

## Production-readiness gate

Missing evidence is **FAIL**. The scaffold documents intent but does not satisfy
any live-platform gate.

| Gate | Current status | Evidence required to pass |
|------|----------------|---------------------------|
| Load | **FAIL** | Arrival/completion targets met at agreed p95 queue wait and error rate |
| Soak | **FAIL** | Sustained representative run with stable memory, queue depth, and error budget |
| Rollback | **FAIL** | Previous image restored within the agreed rollback objective |
| Dependency/failure | **FAIL** | Timeout, Valkey loss, Spaces outage, worker loss, and database reconnect demonstrations |
| Restore | **FAIL** | PostgreSQL restore completes within selected RPO/RTO |
| Security | **FAIL** | Vendor-isolation, upload-validation, secret-scan, and access-log evidence |
| Capacity headroom | **FAIL** | Measured peak retains the agreed spare worker/inference capacity |

No risk acceptance has been granted. Any temporary acceptance must name an
owner, expiry, blast radius, and compensating control.

## Unit-test cost and impact

| Factor | Assessment |
|--------|------------|
| Cloud cost | **$0** — PostgreSQL, Valkey, Spaces, and inference clients are mocked |
| Engineering cost | Approximately **2–4 hours** for the simulation’s high-risk paths |
| CI cost | Seconds to a few minutes per change |
| Primary impact | Detect duplicate/lost-job logic, timeout, and retry regressions before deployment |
| What it cannot prove | Real service integration, load capacity, database failover, backup restore, or rolling-deploy behavior |

Unit tests are the first gate, not the entire production-readiness claim.

## Not evidence

- Architecture diagrams alone
- An empty DOKS cluster
- “It works on my laptop”

## Ownership

FDE produces the pack after Dana locks checklist answers and ADR-001.
