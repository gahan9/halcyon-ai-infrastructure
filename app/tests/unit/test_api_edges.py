# SPDX-License-Identifier: MIT
"""Additional API edge-path tests."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from halcyon_sim.api import create_app
from halcyon_sim.auth import FakeAuthProvider
from halcyon_sim.config import AppEnvironment, Settings
from halcyon_sim.jobs import InMemoryJobRepository
from halcyon_sim.queue import InMemoryJobQueue, QueueUnavailableError
from halcyon_sim.storage import InMemoryObjectStorage


class FailingJobs:
    async def insert(self, job):  # type: ignore[no-untyped-def]
        raise RuntimeError("db down")


class UnavailableQueue(InMemoryJobQueue):
    """Queue double that fails after the job is durably inserted."""

    async def enqueue(self, job_id: UUID) -> None:
        del job_id
        raise QueueUnavailableError("queue unavailable")


@pytest.mark.asyncio
async def test_compensating_delete_on_insert_failure() -> None:
    settings = Settings(
        _env_file=None,
        sim_work_min_seconds=0,
        sim_work_max_seconds=0,
    )
    storage = InMemoryObjectStorage()
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
        jobs=FailingJobs(),  # type: ignore[arg-type]
        queue=InMemoryJobQueue(),
        storage=storage,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with pytest.raises(RuntimeError, match="db down"):
            await client.post(
                "/v1/contracts",
                headers={"Authorization": "Bearer vendor-a"},
                files={"file": ("a.pdf", b"%PDF-1.4\n%EOF", "application/pdf")},
            )
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_presign_happy_path() -> None:
    settings = Settings(_env_file=None)
    jobs = InMemoryJobRepository()
    storage = InMemoryObjectStorage()
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
        jobs=jobs,
        queue=InMemoryJobQueue(),
        storage=storage,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/v1/contracts",
            headers={"Authorization": "Bearer vendor-a"},
            files={"file": ("a.pdf", b"%PDF-1.4\n%EOF", "application/pdf")},
        )
        job_id = created.json()["job_id"]
        response = await client.post(
            f"/v1/contracts/{job_id}/presign",
            headers={"Authorization": "Bearer vendor-a"},
        )
        denied = await client.post(
            f"/v1/contracts/{job_id}/presign?ttl_seconds=999999",
            headers={"Authorization": "Bearer vendor-a"},
        )
        missing = await client.post(
            f"/v1/contracts/{uuid4()}/presign",
            headers={"Authorization": "Bearer vendor-a"},
        )
    assert response.status_code == 200
    assert "url" in response.json()
    assert denied.status_code == 400
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_upload_queue_unavailable_returns_202_for_reconciliation() -> None:
    settings = Settings(_env_file=None)
    jobs = InMemoryJobRepository()
    app = create_app(
        settings=settings,
        auth=FakeAuthProvider(app_env=AppEnvironment.LOCAL),
        jobs=jobs,
        queue=UnavailableQueue(),
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
    persisted = await jobs.get_by_id(UUID(response.json()["job_id"]))
    assert persisted is not None
