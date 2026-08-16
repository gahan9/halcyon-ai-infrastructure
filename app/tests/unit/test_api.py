# SPDX-License-Identifier: MIT
"""API upload/status contract tests with in-memory adapters."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from halcyon_sim.api import create_app
from halcyon_sim.auth import FakeAuthProvider
from halcyon_sim.config import AppEnvironment, Settings
from halcyon_sim.jobs import InMemoryJobRepository, JobStatus
from halcyon_sim.queue import InMemoryJobQueue
from halcyon_sim.storage import InMemoryObjectStorage


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        sim_work_min_seconds=0,
        sim_work_max_seconds=0,
        upload_scan_required=False,
    )


@pytest.mark.asyncio
async def test_upload_returns_202_and_enqueues(settings: Settings) -> None:
    jobs = InMemoryJobRepository()
    queue = InMemoryJobQueue()
    storage = InMemoryObjectStorage()
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
        jobs=jobs,
        queue=queue,
        storage=storage,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/contracts",
            headers={"Authorization": "Bearer vendor-a"},
            files={"file": ("contract.pdf", b"%PDF-1.4\n%EOF", "application/pdf")},
        )
    assert response.status_code == 202
    body = response.json()
    job_id = body["job_id"]
    assert body["status"] == JobStatus.ACCEPTED.value
    assert len(queue.pending) == 1
    stored = await jobs.get_by_id(__import__("uuid").UUID(job_id))
    assert stored is not None
    assert stored.object_key in storage.objects


@pytest.mark.asyncio
async def test_vendor_isolation_on_status(settings: Settings) -> None:
    jobs = InMemoryJobRepository()
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
        jobs=jobs,
        queue=InMemoryJobQueue(),
        storage=InMemoryObjectStorage(),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/v1/contracts",
            headers={"Authorization": "Bearer vendor-a"},
            files={"file": ("a.pdf", b"%PDF-1.4\n%EOF", "application/pdf")},
        )
        job_id = created.json()["job_id"]
        denied = await client.get(
            f"/v1/contracts/{job_id}",
            headers={"Authorization": "Bearer vendor-b"},
        )
        allowed = await client.get(
            f"/v1/contracts/{job_id}",
            headers={"Authorization": "Bearer vendor-a"},
        )
    assert denied.status_code == 404
    assert allowed.status_code == 200


@pytest.mark.asyncio
async def test_reject_non_pdf(settings: Settings) -> None:
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
        jobs=InMemoryJobRepository(),
        queue=InMemoryJobQueue(),
        storage=InMemoryObjectStorage(),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/contracts",
            headers={"Authorization": "Bearer vendor-a"},
            files={"file": ("x.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_quarantine_when_scan_required() -> None:
    settings = Settings(
        _env_file=None,
        upload_scan_required=True,
        sim_work_min_seconds=0,
        sim_work_max_seconds=0,
    )
    queue = InMemoryJobQueue()
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
        jobs=InMemoryJobRepository(),
        queue=queue,
        storage=InMemoryObjectStorage(),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/contracts",
            headers={"Authorization": "Bearer vendor-a"},
            files={"file": ("a.pdf", b"%PDF-1.4\n%EOF", "application/pdf")},
        )
    assert response.status_code == 202
    assert response.json()["status"] == JobStatus.QUARANTINED.value
    assert queue.pending == []


@pytest.mark.asyncio
async def test_healthz(settings: Settings) -> None:
    app = create_app(settings=settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_missing_job_status(settings: Settings) -> None:
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/v1/contracts/{uuid4()}",
            headers={"Authorization": "Bearer vendor-a"},
        )
    assert response.status_code == 404
