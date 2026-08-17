#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Build, push, and deploy the production App Platform app using WSL doctl.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROD_TF="$ROOT/infra/terraform/environments/production"
SPEC_DIR="${HALCYON_PROD_DEPLOY_DIR:-$HOME/halcyon-production-deploy}"
DOCTL_CONTEXT="${DOCTL_CONTEXT:-admin}"
REGISTRY="${HALCYON_REGISTRY:-halcyonstg202608161050}"
IMAGE_TAG="${HALCYON_IMAGE_TAG:-production-$(date -u +%Y%m%d%H%M%S)}"
APP_NAME="${HALCYON_PROD_APP_NAME:-halcyon-sim-production}"
SKIP_IMAGE_BUILD="${SKIP_IMAGE_BUILD:-0}"

doctl_cmd() {
  doctl --context "$DOCTL_CONTEXT" "$@"
}

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

need doctl
need python3
need terraform
need docker

docker_cmd() {
  if docker info >/dev/null 2>&1; then
    docker "$@"
  else
    sudo docker "$@"
  fi
}

: "${DIGITALOCEAN_TOKEN:?source ~/halcyon-tfstate-backend.env first}"
: "${SPACES_ACCESS_KEY_ID:?source ~/halcyon-tfstate-backend.env first}"
: "${SPACES_SECRET_ACCESS_KEY:?source ~/halcyon-tfstate-backend.env first}"

mkdir -p "$SPEC_DIR"
chmod 700 "$SPEC_DIR"

echo "== terraform outputs =="
cd "$PROD_TF"
terraform init -input=false -backend-config=backend.hcl >/dev/null
PG_ID="$(terraform output -raw postgres_id)"
VK_ID="$(terraform output -raw valkey_id)"
BUCKET="$(terraform output -raw spaces_bucket_name)"
VPC_ID="$(terraform output -raw vpc_id)"

echo "== build and push ${REGISTRY}/halcyon-sim:${IMAGE_TAG} =="
if [[ "$SKIP_IMAGE_BUILD" == "1" ]]; then
  echo "SKIP_IMAGE_BUILD=1 — reusing existing DOCR tag"
else
  doctl_cmd registry login
  IMAGE="registry.digitalocean.com/${REGISTRY}/halcyon-sim:${IMAGE_TAG}"
  docker_cmd build -t "$IMAGE" "$ROOT/app"
  docker_cmd push "$IMAGE"
fi

echo "== database connections =="
doctl_cmd databases connection "$PG_ID" -o json >"$SPEC_DIR/pg-conn.json"
doctl_cmd databases connection "$VK_ID" -o json >"$SPEC_DIR/vk-conn.json"

export HALCYON_IMAGE_TAG="$IMAGE_TAG"
export HALCYON_BUCKET="$BUCKET"
export HALCYON_REGISTRY="$REGISTRY"
export HALCYON_VPC_ID="$VPC_ID"
export SPACES_ACCESS_ID="$SPACES_ACCESS_KEY_ID"
export SPACES_SECRET_KEY="$SPACES_SECRET_ACCESS_KEY"
export HALCYON_APP_NAME="$APP_NAME"
export HALCYON_PROD_DEPLOY_DIR="$SPEC_DIR"

python3 - <<'PY'
import json
import os
from pathlib import Path

spec_dir = Path(os.environ["HALCYON_PROD_DEPLOY_DIR"])
pg = json.loads((spec_dir / "pg-conn.json").read_text())
vk = json.loads((spec_dir / "vk-conn.json").read_text())
if isinstance(pg, list):
    pg = pg[0]
if isinstance(vk, list):
    vk = vk[0]

image_tag = os.environ["HALCYON_IMAGE_TAG"]
bucket = os.environ["HALCYON_BUCKET"]
registry = os.environ["HALCYON_REGISTRY"]
app_name = os.environ["HALCYON_APP_NAME"]

db_url = pg["uri"]
valkey_url = vk["uri"]
if "private-" in db_url or "private-" in valkey_url:
    raise SystemExit("refusing private DB hosts without matching App Platform VPC region")

spaces_json = json.dumps(
    {
        "schema_version": 1,
        "environment": "production",
        "access_key": os.environ["SPACES_ACCESS_ID"],
        "secret_key": os.environ["SPACES_SECRET_KEY"],
    },
    separators=(",", ":"),
)
llm_json = json.dumps(
    {
        "schema_version": 1,
        "environment": "production",
        "api_key": "production-placeholder-until-inference-key",
    },
    separators=(",", ":"),
)

def secret_env(key: str, value: str) -> str:
    return (
        f"      - key: {key}\n"
        f"        scope: RUN_TIME\n"
        f"        type: SECRET\n"
        f"        value: {json.dumps(value)}\n"
    )

def plain_env(key: str, value: str) -> str:
    return (
        f"      - key: {key}\n"
        f"        scope: RUN_TIME\n"
        f"        value: {json.dumps(value)}\n"
    )

common_data = (
    secret_env("DATABASE_URL", db_url)
    + secret_env("VALKEY_URL", valkey_url)
    + plain_env("SPACES_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
    + plain_env("SPACES_BUCKET", bucket)
    + plain_env("SPACES_REGION", "nyc3")
    + secret_env("SPACES_CREDENTIALS_JSON", spaces_json)
)

api_envs = (
    plain_env("APP_ENV", "production")
    + plain_env("APP_PORT", "8080")
    + plain_env("AUTH_MODE", "fail_closed")
    + plain_env("UPLOAD_SCAN_REQUIRED", "false")
    + plain_env("SIMULATED_TIMEOUT_RATE", "0")
    + plain_env("SIMULATED_FAILURE_RATE", "0")
    + common_data
)

worker_envs = (
    plain_env("APP_ENV", "production")
    + plain_env("AUTH_MODE", "fail_closed")
    + plain_env("WORKER_CONCURRENCY", "2")
    + plain_env("INFERENCE_MAX_CONCURRENCY", "10")
    + plain_env("INFERENCE_TIMEOUT_SECONDS", "240")
    + plain_env("JOB_MAX_RETRIES", "3")
    + plain_env("JOB_LEASE_SECONDS", "570")
    + plain_env("WORKER_GRACE_PERIOD_SECONDS", "600")
    + plain_env("SIMULATED_TIMEOUT_RATE", "0")
    + plain_env("SIMULATED_FAILURE_RATE", "0")
    + plain_env("LLM_BASE_URL", "https://inference.do-ai.run")
    + plain_env("LLM_MODEL", "local-fake")
    + secret_env("LLM_CREDENTIALS_JSON", llm_json)
    + common_data
)

spec = f"""name: {app_name}
region: nyc
features:
  - buildpack-stack=ubuntu-22
services:
  - name: api
    image:
      registry_type: DOCR
      registry: {registry}
      repository: halcyon-sim
      tag: "{image_tag}"
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8080
    health_check:
      http_path: /healthz
      initial_delay_seconds: 20
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 12
    envs:
{api_envs.rstrip()}
    run_command: python -m halcyon_sim.api
workers:
  - name: worker
    image:
      registry_type: DOCR
      registry: {registry}
      repository: halcyon-sim
      tag: "{image_tag}"
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
{worker_envs.rstrip()}
    run_command: python -m halcyon_sim.worker
"""

out = spec_dir / "app-spec.yaml"
out.write_text(spec, encoding="utf-8")
out.chmod(0o600)
print(f"SPEC_OK bytes={out.stat().st_size} tag={image_tag}")
print(f"PG_HOST={pg['host']}")
print(f"VK_HOST={vk['host']}")
PY

SPEC_FILE="$SPEC_DIR/app-spec.yaml"
EXISTING="$(doctl_cmd apps list -o json | python3 -c '
import json,sys
name=sys.argv[1]
for app in json.load(sys.stdin):
    spec=app.get("spec") or {}
    if spec.get("name")==name:
        print(app["id"]); break
' "$APP_NAME")"

if [[ -n "$EXISTING" ]]; then
  echo "Updating app ${EXISTING}"
  doctl_cmd apps update "$EXISTING" --spec "$SPEC_FILE" -o json >"$SPEC_DIR/app-update.json"
  APP_ID="$EXISTING"
else
  echo "Creating app ${APP_NAME}"
  doctl_cmd apps create --spec "$SPEC_FILE" -o json >"$SPEC_DIR/app-create.json"
  APP_ID="$(python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); item=data[0] if isinstance(data,list) else data; print(item["id"])' "$SPEC_DIR/app-create.json")"
fi

echo "APP_ID=${APP_ID}"
doctl_cmd databases firewalls append "$PG_ID" --rule "app:${APP_ID}" || true
doctl_cmd databases firewalls append "$VK_ID" --rule "app:${APP_ID}" || true

echo "Waiting for deployment..."
for _ in $(seq 1 80); do
  STATUS="$(doctl_cmd apps get "$APP_ID" -o json | python3 -c '
import json,sys
a=json.load(sys.stdin)
if isinstance(a, list):
    a=a[0]
dep=a.get("active_deployment") or a.get("in_progress_deployment") or {}
phase=dep.get("phase") or "UNKNOWN"
live=a.get("live_url") or a.get("default_ingress") or ""
print(f"{phase}|{live}")
')"
  PHASE="${STATUS%%|*}"
  LIVE="${STATUS#*|}"
  echo "phase=${PHASE} live=${LIVE}"
  if [[ "$PHASE" == "ACTIVE" && -n "$LIVE" ]]; then
    echo "DEPLOY_OK app_id=${APP_ID} url=${LIVE} tag=${IMAGE_TAG}"
    exit 0
  fi
  if [[ "$PHASE" == "ERROR" || "$PHASE" == "CANCELED" ]]; then
    echo "DEPLOY_FAILED phase=${PHASE}" >&2
    exit 1
  fi
  sleep 15
done

echo "DEPLOY_TIMEOUT" >&2
exit 1
