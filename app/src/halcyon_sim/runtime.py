# SPDX-License-Identifier: MIT
"""Compose API/worker collaborators from settings."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from halcyon_sim.config import Settings
from halcyon_sim.faults import FaultPolicy
from halcyon_sim.inference import InferenceClient, build_inference_client
from halcyon_sim.jobs import InMemoryJobRepository, JobRepository
from halcyon_sim.jobs_sql import (
    SqlAlchemyJobRepository,
    create_engine,
    create_session_factory,
)
from halcyon_sim.queue import InMemoryJobQueue, JobQueue, build_job_queue
from halcyon_sim.storage import (
    InMemoryObjectStorage,
    ObjectStorage,
    build_object_storage,
)


@dataclass(frozen=True, slots=True)
class RuntimeStack:
    """Resolved runtime collaborators for API or worker processes."""

    jobs: JobRepository
    queue: JobQueue
    storage: ObjectStorage
    inference: InferenceClient
    engine: AsyncEngine | None
    policy: FaultPolicy


def _spaces_configured(settings: Settings) -> bool:
    return (
        settings.spaces_endpoint is not None
        and settings.spaces_bucket is not None
        and settings.spaces_region is not None
        and settings.spaces_credentials_json is not None
    )


def cloud_backends_requested(settings: Settings) -> bool:
    """True when any managed-cloud setting is present."""

    return (
        settings.database_url is not None
        or settings.valkey_url is not None
        or _spaces_configured(settings)
    )


def build_runtime_stack(settings: Settings) -> RuntimeStack:
    """Wire cloud adapters when fully configured; otherwise local in-memory fakes."""

    policy = FaultPolicy(
        seed=settings.simulation_seed,
        timeout_rate=settings.simulated_timeout_rate,
        failure_rate=settings.simulated_failure_rate,
    )
    wants_cloud = cloud_backends_requested(settings)
    if wants_cloud:
        if settings.database_url is None or settings.valkey_url is None:
            msg = "DATABASE_URL and VALKEY_URL are required together"
            raise ValueError(msg)
        if not _spaces_configured(settings):
            msg = "Spaces settings are incomplete"
            raise ValueError(msg)
        engine = create_engine(settings.database_url.get_secret_value())
        jobs: JobRepository = SqlAlchemyJobRepository(create_session_factory(engine))
        queue = build_job_queue(settings)
        storage = build_object_storage(settings)
        inference = build_inference_client(settings, policy=policy)
        return RuntimeStack(
            jobs=jobs,
            queue=queue,
            storage=storage,
            inference=inference,
            engine=engine,
            policy=policy,
        )

    return RuntimeStack(
        jobs=InMemoryJobRepository(inference_slots=settings.inference_max_concurrency),
        queue=InMemoryJobQueue(),
        storage=InMemoryObjectStorage(),
        inference=build_inference_client(settings, policy=policy),
        engine=None,
        policy=policy,
    )
