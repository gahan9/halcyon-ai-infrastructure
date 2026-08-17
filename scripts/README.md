<!-- SPDX-License-Identifier: MIT -->

# Scripts (deferred)

Operational helpers for staging evidence. Nothing here runs in the scaffold
phase.

## Planned layout

```
scripts/
  README.md
  load/                 # Locust scenarios or thin HTTP clients
  chaos/                # staging-only failure drills
```

## Tooling split

| Directory | Preferred tool | Purpose |
|-----------|----------------|---------|
| `load/` | Locust | Upload/status arrival, soak, concurrency headroom |
| `chaos/` | Custom bash/Python with `set -euo pipefail` | Worker restart, Valkey `job_id` removal, deploy-during-job |

Do not use Locust to inject application timeout/failure outcomes. Those remain
the seeded `halcyon_sim.faults` policy so retry and DLQ evidence stays
deterministic.

## Guards

- Require `--env=staging` (or refuse to run).
- Never target production.
- Never delete Spaces objects or PostgreSQL job rows as chaos actions.
- Capture job ids, attempt history, and queue depth in the evidence artifact.
- Cap Locust concurrency so the run stays within `INFERENCE_MAX_CONCURRENCY`
  and the approved inference prepaid budget.
