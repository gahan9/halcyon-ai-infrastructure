<!-- SPDX-License-Identifier: MIT -->

# Scripts

Operational helpers for Terraform prep and staging/production drills.

## Terraform / deploy

| Script | Purpose |
|--------|---------|
| `bootstrap_tf_state.sh` | Create a Spaces key with WSL `doctl`, bootstrap the state bucket, and write the credential env file |
| `production_tf_prep.sh` | Write `production.tfvars`, remote `init`, `validate`, `plan` (no apply) |
| `production_tf_apply.sh` | Apply reviewed plan only when `CONFIRM_PRODUCTION_APPLY=yes` |
| `merge_nonsecret_env.py` | Merge `deploy/*.nonsecret.env` into local `.env` |
| `fetch_nonsecret_staging.py` | Refresh staging non-secret IDs from live resources |

See [docs/operations/production-prep.md](../docs/operations/production-prep.md).

## Planned layout (evidence drills)

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

- Production apply requires `CONFIRM_PRODUCTION_APPLY=yes`.
- Chaos/load helpers must require `--env=staging` (or refuse to run).
- Never delete Spaces objects or PostgreSQL job rows as chaos actions.
- Capture job ids, attempt history, and queue depth in the evidence artifact.
- Cap Locust concurrency so the run stays within `INFERENCE_MAX_CONCURRENCY`
  and the approved inference prepaid budget.
