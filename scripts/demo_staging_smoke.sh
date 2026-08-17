#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Staging-only upload/status smoke. No secrets required (FakeAuth).
set -euo pipefail

LIVE="${HALCYON_LIVE_URL:-https://halcyon-sim-staging-opauz.ondigitalocean.app}"
LIVE="${LIVE%/}"
TOKEN="${HALCYON_DEMO_BEARER:-staging-demo-token}"

echo "LIVE=$LIVE"

echo "=== healthz ==="
curl -fsS "$LIVE/healthz"
echo

PDF="$(mktemp halcyon-smoke.XXXXXX.pdf)"
trap 'rm -f "$PDF"' EXIT
printf '%%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%%%EOF\n' >"$PDF"

echo "=== upload ==="
RESP="$(curl -fsS -X POST "$LIVE/v1/contracts" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@${PDF};type=application/pdf;filename=smoke.pdf")"
echo "$RESP"
JOB_ID="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["job_id"])' "$RESP")"
echo "JOB_ID=$JOB_ID"

echo "=== status poll ==="
for attempt in $(seq 1 40); do
  ST="$(curl -fsS "$LIVE/v1/contracts/${JOB_ID}" \
    -H "Authorization: Bearer ${TOKEN}")"
  echo "attempt=${attempt} ${ST}"
  STATUS="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["status"])' "$ST")"
  case "$STATUS" in
    succeeded | failed | quarantined)
      echo "SMOKE_DONE status=${STATUS}"
      exit 0
      ;;
  esac
  sleep 3
done

echo "SMOKE_TIMEOUT"
exit 1
