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
[[ -n "${APP_ID:-}" && -n "${WORKER_COMPONENT:-}" ]] || {
  echo "APP_ID and WORKER_COMPONENT are required" >&2
  exit 2
}

echo "DRY RUN ONLY: no worker will be terminated."
echo "Would verify App Platform app ${APP_ID} and component ${WORKER_COMPONENT}."
echo "Would terminate one staging worker through an approved operator mechanism."
echo "Would then use doctl to inspect deployments/logs and confirm the PostgreSQL"
echo "lease returns the interrupted job to accepted/retry for one reconciliation."
