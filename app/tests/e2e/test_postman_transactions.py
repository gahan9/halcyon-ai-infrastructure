# SPDX-License-Identifier: MIT
"""Live staging checks matching the ten Postman collection transactions."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from urllib.parse import urlparse
from uuid import UUID

import httpx
import pytest

PDF_FIXTURE = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
TERMINAL_STATUSES = {"succeeded", "dead_letter", "rejected"}
UNKNOWN_JOB_ID = "00000000-0000-0000-0000-000000000000"

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def live_settings() -> tuple[str, str, str]:
    """Load a guarded live-staging endpoint and two distinct vendor tokens."""

    base_url = os.environ.get("HALCYON_E2E_BASE_URL", "").rstrip("/")
    bearer_token = os.environ.get("HALCYON_E2E_BEARER_TOKEN", "")
    other_vendor_token = os.environ.get("HALCYON_E2E_OTHER_VENDOR_TOKEN", "")
    if not base_url or not bearer_token or not other_vendor_token:
        pytest.skip("HALCYON_E2E_BASE_URL and both E2E bearer tokens are required")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        pytest.fail("HALCYON_E2E_BASE_URL must be an HTTPS origin")
    if "staging" not in parsed.netloc:
        pytest.fail("live e2e tests are restricted to a staging hostname")
    if bearer_token == other_vendor_token:
        pytest.fail("E2E vendor tokens must be distinct")
    return base_url, bearer_token, other_vendor_token


@pytest.fixture(scope="module")
def client(live_settings: tuple[str, str, str]) -> Iterator[httpx.Client]:
    """Provide one bounded HTTP client for the live test module."""

    base_url, _, _ = live_settings
    with httpx.Client(base_url=base_url, timeout=30.0) as live_client:
        yield live_client


def auth(token: str) -> dict[str, str]:
    """Build a bearer header without logging the token."""

    return {"Authorization": f"Bearer {token}"}


def upload_job(client: httpx.Client, token: str) -> str:
    """Upload one deterministic PDF and return its validated job id."""

    response = client.post(
        "/v1/contracts",
        headers=auth(token),
        files={"file": ("e2e.pdf", PDF_FIXTURE, "application/pdf")},
    )
    assert response.status_code == 202, response.text
    body = response.json()
    UUID(body["job_id"])
    assert body["status"] in {"accepted", "quarantined"}
    return str(body["job_id"])


def wait_for_terminal(
    client: httpx.Client, token: str, job_id: str
) -> dict[str, object]:
    """Poll a job every second for at most thirty seconds."""

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        response = client.get(f"/v1/contracts/{job_id}", headers=auth(token))
        assert response.status_code == 200, response.text
        body = response.json()
        if body["status"] in TERMINAL_STATUSES:
            return body
        time.sleep(1)
    pytest.fail(f"job {job_id} did not reach a terminal state within 30 seconds")


def test_transaction_01_upload_pdf(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 1: a valid multipart PDF is accepted asynchronously."""

    _, token, _ = live_settings
    upload_job(client, token)


def test_transaction_02_poll_until_terminal(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 2: a submitted job reaches a documented terminal state."""

    _, token, _ = live_settings
    body = wait_for_terminal(client, token, upload_job(client, token))
    assert body["status"] in TERMINAL_STATUSES


def test_transaction_03_get_job_status(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 3: the owning vendor can retrieve the job contract."""

    _, token, _ = live_settings
    job_id = upload_job(client, token)
    response = client.get(f"/v1/contracts/{job_id}", headers=auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert isinstance(body["attempt_count"], int)


def test_transaction_04_create_presigned_get_url(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 4: presign returns a bounded URL that downloads the PDF."""

    _, token, _ = live_settings
    job_id = upload_job(client, token)
    response = client.post(
        f"/v1/contracts/{job_id}/presign?ttl_seconds=3600", headers=auth(token)
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["job_id"] == job_id
    assert body["expires_in"] == 3600
    download = httpx.get(body["url"], timeout=30.0)
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF-")


def test_transaction_05_health_check(client: httpx.Client) -> None:
    """Postman 5: health is public, JSON, and reports ok."""

    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok"}


def test_transaction_06_reject_missing_bearer_token(client: httpx.Client) -> None:
    """Postman 6: protected status rejects missing authorization."""

    response = client.get(f"/v1/contracts/{UNKNOWN_JOB_ID}")
    assert response.status_code == 401
    assert "Traceback" not in response.text


def test_transaction_07_unknown_job_returns_404(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 7: an unknown UUID returns a generic not-found response."""

    _, token, _ = live_settings
    response = client.get(f"/v1/contracts/{UNKNOWN_JOB_ID}", headers=auth(token))
    assert response.status_code == 404
    assert response.json() == {"detail": "job not found"}


def test_transaction_08_hide_job_from_other_vendor(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 8: another vendor cannot discover the submitted job."""

    _, token, other_token = live_settings
    job_id = upload_job(client, token)
    response = client.get(f"/v1/contracts/{job_id}", headers=auth(other_token))
    assert response.status_code == 404
    assert response.json() == {"detail": "job not found"}


def test_transaction_09_reject_upload_without_file(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 9: upload requires the multipart file field."""

    _, token, _ = live_settings
    response = client.post("/v1/contracts", headers=auth(token))
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_transaction_10_reject_presign_ttl_over_24_hours(
    client: httpx.Client, live_settings: tuple[str, str, str]
) -> None:
    """Postman 10: a TTL above 86400 seconds is rejected."""

    _, token, _ = live_settings
    job_id = upload_job(client, token)
    response = client.post(
        f"/v1/contracts/{job_id}/presign?ttl_seconds=86401", headers=auth(token)
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "ttl too large"}
