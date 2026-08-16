<!-- SPDX-License-Identifier: MIT -->

# Staging bring-up notes (authorized experiment)

Date: 2026-08-16. Scope: **staging only**. Production apply/deploy was not
performed. These notes are operational evidence of a private staging smoke; they
**do not** flip the seven live readiness gates below to PASS.

## What was provisioned (non-secret)

| Resource | Identifier / name |
|----------|-------------------|
| DO project | `halcyon-part1-staging` (`ff00c30c-ba80-4ca8-9f35-d2673ab28141`) |
| VPC | `10.20.0.0/24` nyc3 (`deeba864-9e6d-4ab6-abcb-45ea1b299125`) |
| Managed PostgreSQL | `halcyon-part1-staging-postgres` (`ed49d081-1418-4290-88f3-2ece07a24b4c`) |
| Managed Valkey | `halcyon-part1-staging-valkey` (`5352f28c-cbd1-4f64-905e-dfb558924c44`) |
| Spaces bucket | `halcyon-part1-stg-202608161050` (nyc3) |
| DOCR | `halcyonstg202608161050` |
| App Platform app | `halcyon-sim-staging` (`77e036c6-f6a9-4c9d-a33c-9ff4cf996cb6`) |
| Live URL | `https://halcyon-sim-staging-opauz.ondigitalocean.app` |

Terraform root: `infra/terraform/environments/staging` with **local state** for
this first exercise (remote `backend "s3"` left commented). Spaces credentials
were supplied via `TF_VAR_spaces_*` / env only—never committed.

## Auth / env exception (temporary)

First smoke used `APP_ENV=local` and `AUTH_MODE=local` on the staging-named App
Platform app so `FakeAuthProvider` and `FakeInferenceClient` could run without
an IdP or Serverless Inference key. Tighten to `APP_ENV=staging` /
`AUTH_MODE=fail_closed` (and real inference credentials) once identity is
chosen. Treat the public URL as an exercise endpoint until that flip.

App Platform region slug `nyc` maps to **nyc1**; managed data lives in **nyc3**,
so the app was **not** VPC-attached. Databases trust the App Platform app id via
firewall `app:<app-id>` rules and public hostnames.

## Image / deploy

- Image built from `app/Dockerfile`, pushed to DOCR tag `staging-202608161707`
  (digest recorded in local ops env only).
- App Spec filled outside git (`~/halcyon-staging-deploy/app-spec.yaml` in WSL);
  secrets injected as App Platform `SECRET` envs. API does not receive
  `LLM_CREDENTIALS_JSON`.

## Smoke proof (2026-08-16)

| Check | Result |
|-------|--------|
| `GET /healthz` | `{"status":"ok"}` |
| `POST /v1/contracts` (PDF + `Authorization: Bearer …`) | `202` → `accepted` |
| `GET /v1/contracts/{job_id}` | `running` → `succeeded` with result summary |

Example job id (non-secret): `852e36d7-f05d-4798-a5ea-6623a407d4e3`.

## Security follow-ups

- Rotate any DigitalOcean API token or Spaces key that appeared in terminal
  history during bring-up.
- Do not commit `.env`, `staging.tfvars`, Terraform state, or filled App Specs.
- Prefer snap-visible paths under `$HOME` when feeding specs to `doctl` (snap
  confinement cannot read some `/tmp` paths).

## Live readiness gates

Still **FAIL** for Load, Soak, Rollback, Dependency/failure, Restore, Security,
and Capacity headroom — see [README.md](README.md). Staging smoke is not load,
chaos, restore, or production-ready evidence.
