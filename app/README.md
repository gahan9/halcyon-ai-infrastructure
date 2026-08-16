<!-- SPDX-License-Identifier: MIT -->

# Application simulation

Lightweight workload for the FDE exercise — **not** a real contract parser.

## Behavior

1. Authenticate the caller and derive the vendor identity server-side.
2. Validate a bounded PDF upload; persist it privately to Spaces under an opaque,
   vendor-scoped key.
3. Insert the authoritative PostgreSQL job as `accepted` when scanning is not
   required, or `quarantined` when policy requires scanning.
4. Enqueue only an `accepted` job's `job_id` in managed Valkey. A quarantined
   job is never enqueued or read for inference until a scanner durably releases
   it to `accepted`.
5. Return `202 Accepted` with the job id; never hold the upload request open for
   extraction.
6. A worker claims work only through a PostgreSQL lease on `accepted`/`retry`
   jobs. Valkey is a wake transport of opaque `job_id` values, not the claim
   authority. The worker sleeps a seeded **20 seconds – 4 minutes**, then calls
   DigitalOcean Serverless Inference through one async gateway client with a
   240-second hard timeout and a PostgreSQL-enforced provisional fleet-wide
   concurrency cap of 10.
7. An injected fault policy deterministically selects success, timeout, or
   failure in tests/staging. Simulation is disabled and guarded in production.
8. Workers are idempotent, acknowledge the queue item only after durable state,
   and allow the initial attempt plus at most three retries. Exhausted jobs are
   dead-lettered in PostgreSQL and reported as terminal failures.

## Selected stack

| Concern | Selection |
|---------|-----------|
| API | Python 3.12+, FastAPI, Uvicorn |
| HTTP / inference | Async `httpx` client, configurable OpenAI-compatible endpoint |
| Job ledger / DLQ | Managed PostgreSQL via async SQLAlchemy + `asyncpg` |
| Queue | Managed Valkey via `redis` asyncio client (wake/ack only) |
| Object storage | Private DigitalOcean Spaces via an async-safe S3 adapter |
| Configuration | `pydantic-settings`; private database/Valkey bindables plus scoped Spaces/inference JSON secrets parsed at runtime into `SecretStr` fields and never persisted/logged |
| Tests | pytest, seeded fault policy, mocked HTTP/database/storage clients |
| Load / soak | Locust against staging API only; not a substitute for app fault injection |
| Failure drills | Small staging-only scripts for worker kill, queue-item loss, and deploy drain |

RabbitMQ/Celery and Kafka are intentionally excluded. DigitalOcean does not
provide managed RabbitMQ, and event-stream replay is **not** a requirement for
this simulation. PostgreSQL reconciliation recovers lost Valkey wake items.

## Layout

```
app/
  README.md
  pyproject.toml
  Dockerfile
  src/halcyon_sim/
    __init__.py
    __main__.py
    api.py          # FastAPI — upload/status transport only
    auth.py         # principal → immutable vendor_id
    config.py       # validated settings and production fault guard
    worker.py
    inference.py    # single OpenAI-compatible async gateway with timeout
    jobs.py         # PostgreSQL ledger/state machine
    queue.py        # Valkey job-id wake transport
    storage.py      # private Spaces upload/download boundary
    faults.py       # deterministic injected outcomes
    pdf_validate.py # bounded PDF signature/size checks
  tests/
    unit/
    integration/
```

## Entry points

- API: `python -m halcyon_sim.api`
- Worker: `python -m halcyon_sim.worker`

## Non-goals

- No live DigitalOcean apply, deploy, or evidence collection without approved
  spend and checklist decisions.
- No real contract parser / OCR quality work.
- No DOKS or Part 2 GPU serving in this package.
