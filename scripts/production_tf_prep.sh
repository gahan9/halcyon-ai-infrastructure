#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Prepare production Terraform: generate tfvars, init remote backend, validate,
# and write a reviewed plan. Never applies. Refuse if CONFIRM is wrong on apply
# helper paths.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROD="$ROOT/infra/terraform/environments/production"
TIMESTAMP="${HALCYON_PROD_TIMESTAMP:-$(date -u +%Y%m%d%H%M%S)}"
TFVARS="$PROD/production.tfvars"
PLAN_OUT="${HALCYON_PROD_PLAN_OUT:-$PROD/tfplan}"
EXAMPLE="$PROD/production.tfvars.example"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

need terraform
need doctl

if [[ ! -f "$EXAMPLE" ]]; then
  echo "missing $EXAMPLE" >&2
  exit 1
fi

: "${DIGITALOCEAN_TOKEN:?export DIGITALOCEAN_TOKEN (or source bootstrap env file)}"
: "${SPACES_ACCESS_KEY_ID:?export SPACES_ACCESS_KEY_ID (DigitalOcean Spaces key)}"
: "${SPACES_SECRET_ACCESS_KEY:?export SPACES_SECRET_ACCESS_KEY (DigitalOcean Spaces key)}"

# Spaces credentials, exported under the two naming schemes Terraform expects:
# TF_VAR_* for the DigitalOcean provider, AWS_* for the S3-protocol state
# backend. Both carry the same DigitalOcean Spaces key; no AWS account is used.
export TF_VAR_spaces_access_id="$SPACES_ACCESS_KEY_ID"
export TF_VAR_spaces_secret_key="$SPACES_SECRET_ACCESS_KEY"
export AWS_ACCESS_KEY_ID="$SPACES_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$SPACES_SECRET_ACCESS_KEY"
export AWS_EC2_METADATA_DISABLED=true

cd "$PROD"

if [[ ! -f "$TFVARS" ]]; then
  echo "== write $TFVARS from example (timestamp=$TIMESTAMP) =="
  sed "s/TIMESTAMP/${TIMESTAMP}/g" "$EXAMPLE" >"$TFVARS"
  chmod 600 "$TFVARS"
else
  echo "== reuse existing $TFVARS =="
fi

echo "== terraform init (remote backend) =="
terraform init -input=false -backend-config=backend.hcl

echo "== terraform validate =="
terraform validate

echo "== terraform plan =="
terraform plan -var-file="$TFVARS" -out="$PLAN_OUT" -input=false

echo "PLAN_OK path=$PLAN_OUT"
echo "Review the plan, then apply only with explicit approval:"
echo "  CONFIRM_PRODUCTION_APPLY=yes bash $ROOT/scripts/production_tf_apply.sh"
echo "Do not apply from CI without a protected environment + human approval gate."
