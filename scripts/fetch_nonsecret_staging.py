# SPDX-License-Identifier: MIT
"""Fetch non-secret staging metadata via doctl; never print passwords or URIs with creds."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PG_ID = "ed49d081-1418-4290-88f3-2ece07a24b4c"
VK_ID = "5352f28c-cbd1-4f64-905e-dfb558924c44"
APP_ID = "77e036c6-f6a9-4c9d-a33c-9ff4cf996cb6"
ROOT = Path(__file__).resolve().parents[1]


def run_doctl(args: list[str]) -> object:
    cmd = ["wsl", "-e", "bash", "-lc", f"export PATH=/snap/bin:$PATH; doctl {' '.join(args)}"]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        # retry with admin context
        cmd = [
            "wsl",
            "-e",
            "bash",
            "-lc",
            f"export PATH=/snap/bin:$PATH; doctl --context admin {' '.join(args)}",
        ]
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(proc.stdout)


def first(obj: object) -> dict:
    if isinstance(obj, list):
        return obj[0]
    assert isinstance(obj, dict)
    return obj


def main() -> int:
    tf_state = ROOT / "infra/terraform/environments/staging"
    print("=== terraform outputs ===")
    tf = subprocess.run(
        ["wsl", "-e", "bash", "-lc", f"cd {tf_state.as_posix()} && terraform output -json"],
        capture_output=True,
        text=True,
        check=False,
    )
    tf_out: dict = {}
    if tf.returncode == 0 and tf.stdout.strip():
        tf_out = json.loads(tf.stdout)
        for k, v in tf_out.items():
            print(f"{k}={v.get('value')}")
    else:
        print("TF_OUTPUT_UNAVAILABLE")

    print("\n=== databases ===")
    pg = first(run_doctl(["databases", "get", PG_ID, "-o", "json"]))
    vk = first(run_doctl(["databases", "get", VK_ID, "-o", "json"]))
    pc = pg.get("connection") or {}
    pp = pg.get("private_connection") or {}
    vc = vk.get("connection") or {}
    vp = vk.get("private_connection") or {}
    meta = {
        "PG_HOST": pc.get("host"),
        "PG_PRIVATE_HOST": pp.get("host") or (tf_out.get("postgres_private_host") or {}).get("value"),
        "PG_PORT": pc.get("port") or (tf_out.get("postgres_port") or {}).get("value"),
        "PG_DB": pc.get("database"),
        "PG_USER": pc.get("user"),
        "VK_HOST": vc.get("host"),
        "VK_PRIVATE_HOST": vp.get("host") or (tf_out.get("valkey_private_host") or {}).get("value"),
        "VK_PORT": vc.get("port") or (tf_out.get("valkey_port") or {}).get("value"),
        "VK_USER": vc.get("user"),
        "SPACES_BUCKET": (tf_out.get("spaces_bucket_name") or {}).get("value"),
        "SPACES_ENDPOINT": "https://nyc3.digitaloceanspaces.com",
        "SPACES_REGION": "nyc3",
        "REGISTRY_NAME": (tf_out.get("registry_name") or {}).get("value"),
        "REGISTRY_ENDPOINT": (tf_out.get("registry_endpoint") or {}).get("value"),
        "PROJECT_ID": (tf_out.get("project_id") or {}).get("value"),
        "VPC_ID": (tf_out.get("vpc_id") or {}).get("value"),
        "POSTGRES_ID": PG_ID,
        "VALKEY_ID": VK_ID,
        "APP_ID": APP_ID,
    }
    for k, v in meta.items():
        print(f"{k}={v}")

    print("\n=== app non-secret envs ===")
    app = first(run_doctl(["apps", "get", APP_ID, "-o", "json"]))
    print(f"LIVE_URL={app.get('live_url')}")
    spec = app.get("spec") or {}
    print(f"APP_NAME={spec.get('name')}")
    print(f"APP_REGION={spec.get('region')}")
    app_envs: dict[str, str] = {}
    for kind in ("services", "workers"):
        for svc in spec.get(kind) or []:
            img = svc.get("image") or {}
            print(
                f"IMAGE_{svc.get('name')}="
                f"{img.get('registry')}/{img.get('repository')}:{img.get('tag')}"
            )
            for env in svc.get("envs") or []:
                if env.get("type") == "SECRET":
                    print(f"HAS_SECRET {svc.get('name')} {env.get('key')}")
                else:
                    key = env.get("key")
                    val = env.get("value")
                    print(f"ENV {svc.get('name')} {key}={val}")
                    if key and val is not None and key not in app_envs:
                        app_envs[key] = str(val)

    out = ROOT / "deploy" / "staging.nonsecret.env"
    lines = [
        "# SPDX-License-Identifier: MIT",
        "# Non-secret staging values for local .env / App Spec fill.",
        "# SECRETS stay out of this file: DATABASE_URL, VALKEY_URL,",
        "# SPACES_CREDENTIALS_JSON, LLM_CREDENTIALS_JSON, DIGITALOCEAN_TOKEN.",
        "# Copy non-secret keys into .env; inject secrets via App Platform SECRET",
        "# or a gitignored .env you fill manually from doctl connection URIs.",
        "",
        "# --- Application (local exercise defaults; staging App Spec uses staging/fail_closed) ---",
        "APP_LOG_LEVEL=INFO",
        "APP_PORT=8080",
        "APP_ENV=local",
        "AUTH_MODE=local",
        "",
        "# --- Staging infrastructure (non-secret) ---",
        f"HALCYON_PROJECT_ID={meta['PROJECT_ID']}",
        f"HALCYON_VPC_ID={meta['VPC_ID']}",
        f"HALCYON_POSTGRES_ID={meta['POSTGRES_ID']}",
        f"HALCYON_VALKEY_ID={meta['VALKEY_ID']}",
        f"HALCYON_APP_ID={meta['APP_ID']}",
        f"HALCYON_LIVE_URL={app.get('live_url')}",
        f"HALCYON_REGISTRY={meta['REGISTRY_NAME']}",
        f"HALCYON_REGISTRY_ENDPOINT={meta['REGISTRY_ENDPOINT']}",
        f"HALCYON_IMAGE_REPOSITORY=halcyon-sim",
        f"HALCYON_IMAGE_TAG=staging-202608161707",
        "",
        "# --- Hosts (fill passwords into DATABASE_URL / VALKEY_URL yourself) ---",
        f"HALCYON_PG_HOST={meta['PG_HOST']}",
        f"HALCYON_PG_PRIVATE_HOST={meta['PG_PRIVATE_HOST']}",
        f"HALCYON_PG_PORT={meta['PG_PORT']}",
        f"HALCYON_PG_DB={meta['PG_DB']}",
        f"HALCYON_PG_USER={meta['PG_USER']}",
        f"HALCYON_VK_HOST={meta['VK_HOST']}",
        f"HALCYON_VK_PRIVATE_HOST={meta['VK_PRIVATE_HOST']}",
        f"HALCYON_VK_PORT={meta['VK_PORT']}",
        f"HALCYON_VK_USER={meta['VK_USER']}",
        "",
        "# --- Runtime non-secret env (matches app Settings / App Spec) ---",
        f"SPACES_ENDPOINT={meta['SPACES_ENDPOINT']}",
        f"SPACES_BUCKET={meta['SPACES_BUCKET']}",
        f"SPACES_REGION={meta['SPACES_REGION']}",
        "PRESIGNED_URL_TTL_SECONDS=3600",
        "PRESIGNED_URL_MAX_TTL_SECONDS=86400",
        "LLM_BASE_URL=https://inference.do-ai.run",
        "LLM_MODEL=your-model-id",
        "WORKER_CONCURRENCY=2",
        "INFERENCE_MAX_CONCURRENCY=10",
        "INFERENCE_TIMEOUT_SECONDS=240",
        "JOB_MAX_RETRIES=3",
        "JOB_LEASE_SECONDS=570",
        "RECONCILE_INTERVAL_SECONDS=60",
        "RECONCILE_BATCH_SIZE=100",
        "WORKER_GRACE_PERIOD_SECONDS=600",
        "UPLOAD_MAX_BYTES=26214400",
        "UPLOAD_SCAN_REQUIRED=false",
        "SIMULATION_SEED=0",
        "SIMULATED_TIMEOUT_RATE=0",
        "SIMULATED_FAILURE_RATE=0",
        "SIM_WORK_MIN_SECONDS=20",
        "SIM_WORK_MAX_SECONDS=240",
        "",
        "# --- Secret placeholders (DO NOT put real values in this committed file) ---",
        f"# DATABASE_URL=postgresql://{meta['PG_USER']}:PASSWORD@{meta['PG_HOST']}:{meta['PG_PORT']}/{meta['PG_DB']}?sslmode=require",
        f"# VALKEY_URL=rediss://{meta['VK_USER'] or 'default'}:PASSWORD@{meta['VK_HOST']}:{meta['VK_PORT']}",
        '# SPACES_CREDENTIALS_JSON={"schema_version":1,"environment":"local","access_key":"...","secret_key":"..."}',
        '# LLM_CREDENTIALS_JSON={"schema_version":1,"environment":"local","api_key":"..."}',
        "",
    ]
    # Prefer live app non-secret env overrides when present
    for key in (
        "SPACES_ENDPOINT",
        "SPACES_BUCKET",
        "SPACES_REGION",
        "LLM_BASE_URL",
        "LLM_MODEL",
        "WORKER_CONCURRENCY",
        "APP_PORT",
        "UPLOAD_SCAN_REQUIRED",
    ):
        if key in app_envs:
            # rewrite matching lines
            lines = [
                f"{key}={app_envs[key]}" if line.startswith(f"{key}=") else line
                for line in lines
            ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
