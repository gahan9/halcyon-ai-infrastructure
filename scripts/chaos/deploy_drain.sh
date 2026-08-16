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
[[ -n "${APP_ID:-}" && -n "${IMAGE_DIGEST:-}" ]] || {
  echo "APP_ID and IMAGE_DIGEST are required" >&2
  exit 2
}

echo "DRY RUN ONLY: no App Platform deployment will be started."
echo "Would verify staging app ${APP_ID} and immutable image ${IMAGE_DIGEST}."
echo "Would deploy through protected CI with worker termination grace <=600s."
echo "Would use doctl to inspect deployment health and confirm the in-flight job"
echo "drains or returns to accepted/retry without exceeding the inference cap."
