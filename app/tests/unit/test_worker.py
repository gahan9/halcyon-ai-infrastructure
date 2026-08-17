# SPDX-License-Identifier: MIT
"""Worker lifecycle and reconciliation tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from halcyon_sim.config import Settings
from halcyon_sim.faults import FaultPolicy
from halcyon_sim.inference import FakeInferenceClient
from halcyon_sim.jobs import InMemoryJobRepository, JobStatus, new_job
from halcyon_sim.queue import InMemoryJobQueue
from halcyon_sim.storage import InMemoryObjectStorage
from halcyon_sim.worker import Worker


def _settings(**kwargs: object) -> Settings:
    base: dict[str, object] = {
        "_env_file": None,
        "sim_work_min_seconds": 0.0,
        "sim_work_max_seconds": 0.0,
        "reconcile_interval_seconds": 3600,
    }
    base.update(kwargs)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_worker_success_ack_after_durable_state() -> None:
    settings = _settings()
    jobs = InMemoryJobRepository()
    queue = InMemoryJobQueue()
    storage = InMemoryObjectStorage()
    vendor_id = uuid4()
    job_id = uuid4()
    key = f"vendors/{vendor_id}/jobs/{job_id}/source.pdf"
    await storage.put_pdf(
        vendor_id=vendor_id,
        job_id=job_id,
        content=b"%PDF-1.4\n%EOF",
        content_sha256="abc",
    )
    job = new_job(
        vendor_id=vendor_id,
        object_key=key,
        scan_required=False,
        content_sha256="abc",
        job_id=job_id,
    )
    await jobs.insert(job)
    await queue.enqueue(job.job_id)
    policy = FaultPolicy(seed=0)
    worker = Worker(
        settings=settings,
        jobs=jobs,
        queue=queue,
        storage=storage,
        inference=FakeInferenceClient(policy=policy),
        policy=policy,
    )
    wake_id = await queue.pop_wake()
    assert wake_id == job.job_id
    await worker.process_one(job.job_id)
    saved = await jobs.get_by_id(job.job_id)
    assert saved is not None
    assert saved.status is JobStatus.SUCCEEDED
    assert job.job_id not in queue.processing
    assert job.job_id not in queue.pending


@pytest.mark.asyncio
async def test_worker_timeout_retries_then_can_dead_letter() -> None:
    settings = _settings(job_max_retries=0)
    jobs = InMemoryJobRepository()
    queue = InMemoryJobQueue()
    storage = InMemoryObjectStorage()
    vendor_id = uuid4()
    job_id = uuid4()
    key = f"vendors/{vendor_id}/jobs/{job_id}/source.pdf"
    await storage.put_pdf(
        vendor_id=vendor_id,
        job_id=job_id,
        content=b"%PDF-1.4\n%EOF",
        content_sha256="abc",
    )
    job = new_job(
        vendor_id=vendor_id,
        object_key=key,
        scan_required=False,
        content_sha256="abc",
        max_retries=0,
        job_id=job_id,
    )
    await jobs.insert(job)
    policy = FaultPolicy(seed=1, timeout_rate=1.0)
    worker = Worker(
        settings=settings,
        jobs=jobs,
        queue=queue,
        storage=storage,
        inference=FakeInferenceClient(policy=policy),
        policy=policy,
    )
    await worker.process_one(job_id)
    saved = await jobs.get_by_id(job_id)
    assert saved is not None
    assert saved.status is JobStatus.DEAD_LETTER


@pytest.mark.asyncio
async def test_reconcile_requeues_missing_job_id() -> None:
    settings = _settings()
    jobs = InMemoryJobRepository()
    queue = InMemoryJobQueue()
    job = new_job(
        vendor_id=uuid4(),
        object_key="vendors/a/jobs/b/source.pdf",
        scan_required=False,
    )
    await jobs.insert(job)
    worker = Worker(
        settings=settings,
        jobs=jobs,
        queue=queue,
        storage=InMemoryObjectStorage(),
        inference=FakeInferenceClient(policy=FaultPolicy()),
        policy=FaultPolicy(),
    )
    assert await worker.reconcile_once() == 1
    assert job.job_id in queue.pending
    assert await worker.reconcile_once() == 0


@pytest.mark.asyncio
async def test_inference_slot_cap() -> None:
    jobs = InMemoryJobRepository(inference_slots=1)
    first = await jobs.acquire_inference_slot(slot_count=1)
    second = await jobs.acquire_inference_slot(slot_count=1)
    assert first == 0
    assert second is None
    await jobs.release_inference_slot(0)
    third = await jobs.acquire_inference_slot(slot_count=1)
    assert third == 0
