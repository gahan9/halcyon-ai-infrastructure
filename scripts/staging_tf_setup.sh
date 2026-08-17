#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

ROOT="/mnt/c/Projects/halcyon-ai-infrastructure"
STAGING="$ROOT/infra/terraform/environments/staging"
LOG="/tmp/halcyon-staging-setup.log"
ENVFILE="/tmp/halcyon-staging-env.sh"

exec > >(tee -a "$LOG") 2>&1

cd "$STAGING"
echo "== fix tfvars =="
cat > staging.tfvars <<'EOF'
project_name              = "halcyon-part1-staging"
region                    = "nyc3"
vpc_ip_range              = "10.20.0.0/24"
postgres_version          = "16"
postgres_size             = "db-s-1vcpu-1gb"
postgres_storage_size_mib = 10240
valkey_version            = "8"
valkey_size               = "db-s-1vcpu-1gb"
spaces_bucket_name        = "halcyon-part1-stg-202608161050"
spaces_force_destroy      = true
registry_name             = "halcyonstg202608161050"
registry_subscription_tier_slug = "starter"
EOF
cat staging.tfvars

echo "== token =="
export DIGITALOCEAN_TOKEN
DIGITALOCEAN_TOKEN="$(doctl auth token)"
echo "token length=${#DIGITALOCEAN_TOKEN}"

echo "== spaces keys create =="
if ! KEY_JSON=$(doctl spaces keys create "halcyon-tf-staging-20260816" -o json 2>&1); then
  echo "spaces keys create failed: $KEY_JSON"
  echo "Trying list..."
  doctl spaces keys list -o json || true
else
  export DIGITALOCEAN_ACCESS_ID DIGITALOCEAN_SECRET_KEY
  DIGITALOCEAN_ACCESS_ID="$(printf '%s' "$KEY_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["access_key"])')"
  DIGITALOCEAN_SECRET_KEY="$(printf '%s' "$KEY_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["secret_key"])')"
  echo "spaces access id length=${#DIGITALOCEAN_ACCESS_ID}"
fi

umask 077
{
  echo "export DIGITALOCEAN_TOKEN=$(printf %q "${DIGITALOCEAN_TOKEN}")"
  if [[ -n "${DIGITALOCEAN_ACCESS_ID:-}" ]]; then
    echo "export DIGITALOCEAN_ACCESS_ID=$(printf %q "${DIGITALOCEAN_ACCESS_ID}")"
    echo "export DIGITALOCEAN_SECRET_KEY=$(printf %q "${DIGITALOCEAN_SECRET_KEY}")"
  fi
  echo "export HALCYON_STAGING_BUCKET=halcyon-part1-stg-202608161050"
  echo "export HALCYON_STAGING_REGISTRY=halcyonstg202608161050"
} > "$ENVFILE"
echo "wrote $ENVFILE"

echo "== terraform init/validate/plan =="
rm -rf .terraform
terraform init -input=false
terraform validate
terraform plan -var-file=staging.tfvars -out=tfplan -input=false

echo "== DONE =="
