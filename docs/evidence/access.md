<!-- SPDX-License-Identifier: MIT -->

# Staging access and demo

**Scope:** staging exercise only. Not production-ready. See
[staging bring-up notes](staging-bring-up.md) and the
[evidence gates](README.md).

## Live endpoint

| Item | Value |
|------|-------|
| Base URL | `https://halcyon-sim-staging-opauz.ondigitalocean.app` |
| Health (no auth) | `GET /healthz` → `{"status":"ok"}` |
| Upload | `POST /v1/contracts` (multipart PDF + Bearer token) |
| Status | `GET /v1/contracts/{job_id}` (Bearer token) |

## Temporary authentication

The staging app currently runs with `APP_ENV=local` and `AUTH_MODE=local`
(FakeAuth). **Any** non-empty Bearer token works; the token string becomes the
vendor id (for example `Bearer vendor-a`). This is intentional for the exercise
and must be replaced with a real identity provider before production.

Versioned App Specs in `deploy/` use `AUTH_MODE=fail_closed` for the target
state. Live staging intentionally diverges until Dana chooses an IdP — see
[staging bring-up notes](staging-bring-up.md#auth--env-exception-temporary).

Inference on staging uses a fake client unless real Serverless Inference
credentials are injected. Upload → queue → worker → status still exercises the
async path.

## Try it with curl

Replace `vendor-a` with any label. Use a small PDF file on disk.

```bash
BASE="https://halcyon-sim-staging-opauz.ondigitalocean.app"
TOKEN="vendor-a"

curl -fsS "$BASE/healthz"
echo

curl -fsS -X POST "$BASE/v1/contracts" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@./sample.pdf;type=application/pdf;filename=sample.pdf"

# Copy job_id from the JSON response, then:
curl -fsS "$BASE/v1/contracts/{job_id}" \
  -H "Authorization: Bearer $TOKEN"
```

Minimal inline PDF (for quick smoke without a file):

```bash
printf '%%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%%%EOF\n' > /tmp/smoke.pdf
curl -fsS -X POST "$BASE/v1/contracts" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/smoke.pdf;type=application/pdf;filename=smoke.pdf"
```

Poll until `status` is `succeeded`, `failed`, or `quarantined` (typically under
two minutes on staging with fake inference).

## Scripted smoke

From the repository root:

```bash
export HALCYON_LIVE_URL="https://halcyon-sim-staging-opauz.ondigitalocean.app"
bash scripts/demo_staging_smoke.sh
```

## What this does not prove

Staging smoke does **not** satisfy load, soak, rollback, dependency failure,
restore, security, or capacity-headroom gates. Those remain **FAIL** until
measured evidence is attached under [docs/evidence/](README.md).
