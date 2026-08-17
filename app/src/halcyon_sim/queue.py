# SPDX-License-Identifier: MIT
"""Valkey job-id wake transport (not the claim authority)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from redis.asyncio import Redis

from halcyon_sim.config import Settings

PENDING_KEY = "halcyon:jobs:pending"
PROCESSING_KEY = "halcyon:jobs:processing"


class JobQueue(Protocol):
    """Wake transport for opaque job ids."""

    async def enqueue(self, job_id: UUID) -> None:
        """Offer a job id for workers to wake on."""

    async def pop_wake(self, *, timeout_seconds: int = 5) -> UUID | None:
        """Move one id from pending to processing and return it."""

    async def acknowledge(self, job_id: UUID) -> None:
        """Remove a processing id after durable PostgreSQL state."""

    async def requeue_if_missing(self, job_id: UUID) -> bool:
        """Enqueue when the id is absent from pending and processing."""


class InMemoryJobQueue:
    """Test double with pending/processing semantics."""

    def __init__(self) -> None:
        self.pending: list[UUID] = []
        self.processing: set[UUID] = set()

    async def enqueue(self, job_id: UUID) -> None:
        if job_id not in self.pending and job_id not in self.processing:
            self.pending.append(job_id)

    async def pop_wake(self, *, timeout_seconds: int = 5) -> UUID | None:
        del timeout_seconds
        if not self.pending:
            return None
        job_id = self.pending.pop(0)
        self.processing.add(job_id)
        return job_id

    async def acknowledge(self, job_id: UUID) -> None:
        self.processing.discard(job_id)
        if job_id in self.pending:
            self.pending = [item for item in self.pending if item != job_id]

    async def requeue_if_missing(self, job_id: UUID) -> bool:
        if job_id in self.pending or job_id in self.processing:
            return False
        self.pending.append(job_id)
        return True


class ValkeyJobQueue:  # pragma: no cover - requires live Valkey
    """Managed Valkey list + processing set transport."""

    def __init__(self, client: Redis, *, pending_key: str = PENDING_KEY) -> None:
        self._client = client
        self._pending = pending_key
        self._processing = PROCESSING_KEY

    async def enqueue(self, job_id: UUID) -> None:
        # Avoid duplicates in pending; processing checked by reconciler.
        await self._client.lrem(self._pending, 0, str(job_id))
        await self._client.rpush(self._pending, str(job_id))

    async def pop_wake(self, *, timeout_seconds: int = 5) -> UUID | None:
        item = await self._client.blmove(
            self._pending,
            self._processing,
            timeout=timeout_seconds,
            src="LEFT",
            dest="RIGHT",
        )
        if item is None:
            return None
        if isinstance(item, bytes):
            item = item.decode()
        return UUID(str(item))

    async def acknowledge(self, job_id: UUID) -> None:
        await self._client.lrem(self._processing, 0, str(job_id))
        await self._client.lrem(self._pending, 0, str(job_id))

    async def requeue_if_missing(self, job_id: UUID) -> bool:
        pending = [
            self._decode(v) for v in await self._client.lrange(self._pending, 0, -1)
        ]
        processing = [
            self._decode(v) for v in await self._client.lrange(self._processing, 0, -1)
        ]
        token = str(job_id)
        if token in pending or token in processing:
            return False
        await self._client.rpush(self._pending, token)
        return True

    @staticmethod
    def _decode(value: bytes | str) -> str:
        if isinstance(value, bytes):
            return value.decode()
        return value


def build_job_queue(settings: Settings) -> JobQueue:
    """Build a Valkey queue client from settings."""

    if settings.valkey_url is None:
        msg = "VALKEY_URL is required"
        raise ValueError(msg)
    client = Redis.from_url(
        settings.valkey_url.get_secret_value(),
        decode_responses=False,
        health_check_interval=30,
        socket_connect_timeout=5,
        socket_keepalive=True,
        socket_timeout=10,
    )
    return ValkeyJobQueue(client)
