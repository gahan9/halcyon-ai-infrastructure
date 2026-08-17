#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Apply a previously reviewed production plan. Requires explicit confirmation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROD="$ROOT/infra/terraform/environments/production"
PLAN_OUT="${HALCYON_PROD_PLAN_OUT:-$PROD/tfplan}"

if [[ "${CONFIRM_PRODUCTION_APPLY:-}" != "yes" ]]; then
  echo "Refusing apply. Re-run with CONFIRM_PRODUCTION_APPLY=yes after plan review." >&2
  exit 2
fi

: "${DIGITALOCEAN_TOKEN:?export DIGITALOCEAN_TOKEN}"
: "${SPACES_ACCESS_KEY_ID:?export SPACES_ACCESS_KEY_ID (DigitalOcean Spaces key)}"
: "${SPACES_SECRET_ACCESS_KEY:?export SPACES_SECRET_ACCESS_KEY (DigitalOcean Spaces key)}"

# Same DigitalOcean Spaces key under both names Terraform expects.
export TF_VAR_spaces_access_id="$SPACES_ACCESS_KEY_ID"
export TF_VAR_spaces_secret_key="$SPACES_SECRET_ACCESS_KEY"
export AWS_ACCESS_KEY_ID="$SPACES_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$SPACES_SECRET_ACCESS_KEY"
export AWS_EC2_METADATA_DISABLED=true

if [[ ! -f "$PLAN_OUT" ]]; then
  echo "missing plan at $PLAN_OUT — run scripts/production_tf_prep.sh first" >&2
  exit 1
fi

cd "$PROD"
terraform apply -input=false "$PLAN_OUT"
echo "APPLY_OK"
terraform output
echo "Next: fill deploy/production.nonsecret.env from outputs, build/push image,"
echo "inject App Spec SECRETs, then doctl apps create|update (see docs/operations/production-prep.md)."
