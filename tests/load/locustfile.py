# SPDX-License-Identifier: MIT
"""Paced upload and status load scenarios for staging only.

Set STAGING_API_BASE_URL and STAGING_API_BEARER_TOKEN in the process
environment. Never use production URLs or production credentials.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from locust import HttpUser, constant_pacing, task

TERMINAL_STATUSES = {"succeeded", "dead_letter", "rejected"}
PDF_FIXTURE = b"%PDF-1.4\n%%EOF\n"


def staging_settings() -> tuple[str, str]:
    """Return validated staging-only load-test settings."""

    base_url = os.environ.get("STAGING_API_BASE_URL", "").rstrip("/")
    token = os.environ.get("STAGING_API_BEARER_TOKEN", "")
    parsed = urlparse(base_url)
    if os.environ.get("LOAD_ENV") != "staging":
        raise RuntimeError("LOAD_ENV=staging is required")
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("STAGING_API_BASE_URL must be an HTTPS URL")
    if not token:
        raise RuntimeError("STAGING_API_BEARER_TOKEN is required")
    return base_url, token


class UploadAndStatusUser(HttpUser):
    """Upload PDFs and poll their vendor-scoped status at a bounded pace."""

    host = os.environ.get("STAGING_API_BASE_URL", "https://staging.invalid")
    wait_time = constant_pacing(5.0)

    def on_start(self) -> None:
        """Load credentials without logging them."""

        self.host, token = staging_settings()
        self.headers = {"Authorization": f"Bearer {token}"}
        self.job_ids: list[str] = []

    @task(1)
    def upload_contract(self) -> None:
        """Submit one small PDF and retain its job id for status polling."""

        with self.client.post(
            "/v1/contracts",
            headers=self.headers,
            files={"file": ("load-test.pdf", PDF_FIXTURE, "application/pdf")},
            name="/v1/contracts",
            catch_response=True,
        ) as response:
            if response.status_code != 202:
                response.failure(f"expected 202, got {response.status_code}")
                return
            job_id = response.json().get("job_id")
            if not job_id:
                response.failure("202 response omitted job_id")
                return
            self.job_ids.append(job_id)

    @task(4)
    def check_status(self) -> None:
        """Poll a submitted job without turning a missing job into load."""

        if not self.job_ids:
            return
        job_id = self.job_ids[0]
        with self.client.get(
            f"/v1/contracts/{job_id}",
            headers=self.headers,
            name="/v1/contracts/[job_id]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"expected 200, got {response.status_code}")
                return
            if response.json().get("status") in TERMINAL_STATUSES:
                self.job_ids.pop(0)
