#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

[[ "${1:-}" == "--env=staging" ]] || {
  echo "usage: $0 --env=staging" >&2
  exit 2
}
command -v doctl >/dev/null || {
  echo "doctl is required; authenticate it with staging-only access" >&2
  exit 1
}
[[ -n "${APP_ID:-}" && -n "${JOB_ID:-}" ]] || {
  echo "APP_ID and JOB_ID are required" >&2
  exit 2
}

echo "DRY RUN ONLY: no Valkey item or durable data will be removed."
echo "Would verify staging app ${APP_ID} and PostgreSQL job ${JOB_ID}."
echo "Would invoke an approved, job-scoped staging fault hook to omit one Valkey"
echo "wake item; no such hook is implemented, so the destructive step is blocked."
echo "Would use doctl logs to confirm reconciliation re-enqueues the durable job once."
