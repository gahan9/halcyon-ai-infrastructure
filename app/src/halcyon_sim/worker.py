# SPDX-License-Identifier: MIT
"""Asynchronous worker: lease from PostgreSQL, wake via Valkey."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from dataclasses import dataclass
from uuid import UUID

from halcyon_sim.config import Settings
from halcyon_sim.faults import FaultOutcome, FaultPolicy
from halcyon_sim.inference import (
    InferenceClient,
    InferenceError,
    InferenceErrorKind,
)
from halcyon_sim.jobs import (
    CLAIMABLE,
    JobAttempt,
    JobRepository,
    JobStatus,
    complete_retryable_failure,
    complete_success,
    complete_terminal_failure,
)
from halcyon_sim.jobs_sql import create_schema
from halcyon_sim.queue import JobQueue
from halcyon_sim.runtime import build_runtime_stack
from halcyon_sim.storage import ObjectStorage

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Worker:
    """Bounded concurrent job processor."""

    settings: Settings
    jobs: JobRepository
    queue: JobQueue
    storage: ObjectStorage
    inference: InferenceClient
    policy: FaultPolicy
    owner: str = "worker-1"
    _stopping: bool = False
    _in_flight: int = 0

    async def run_forever(self) -> None:  # pragma: no cover - long-running loop
        """Process wake items until stopped."""

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(NotImplementedError):
                loop.add_signal_handler(sig, self.request_stop)

        reconcile_task = asyncio.create_task(self._reconcile_loop(), name="reconcile")
        try:
            while not self._stopping:
                if self._in_flight >= self.settings.worker_concurrency:
                    await asyncio.sleep(0.05)
                    continue
                job_id = await self.queue.pop_wake(timeout_seconds=1)
                if job_id is None:
                    continue
                self._in_flight += 1
                asyncio.create_task(self._process_guarded(job_id), name=f"job-{job_id}")
            deadline = (
                asyncio.get_running_loop().time()
                + self.settings.worker_grace_period_seconds
            )
            while self._in_flight > 0 and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.1)
        finally:
            reconcile_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await reconcile_task

    def request_stop(self) -> None:
        """Begin graceful shutdown."""

        self._stopping = True

    async def _process_guarded(self, job_id: UUID) -> None:
        try:
            await self.process_one(job_id)
        finally:
            self._in_flight -= 1

    async def process_one(self, job_id: UUID) -> None:
        """Claim, work, persist, then acknowledge the wake item."""

        claimed = await self.jobs.claim(
            job_id,
            owner=self.owner,
            lease_seconds=self.settings.job_lease_seconds,
        )
        if claimed is None:
            await self.queue.acknowledge(job_id)
            return

        delay = self.policy.work_seconds(
            str(claimed.job_id),
            self.settings.sim_work_min_seconds,
            self.settings.sim_work_max_seconds,
        )
        if delay > 0:
            await asyncio.sleep(delay)

        outcome = self.policy.choose(str(claimed.job_id))
        if outcome is FaultOutcome.TIMEOUT:
            updated = complete_retryable_failure(claimed, reason="injected timeout")
            await self.jobs.save(updated)
            await self.jobs.record_attempt(
                JobAttempt(
                    job_id=claimed.job_id,
                    attempt_number=claimed.attempt_count,
                    outcome="timeout",
                    detail="injected timeout",
                )
            )
            await self.queue.acknowledge(job_id)
            if updated.status is JobStatus.RETRY:
                await self.queue.enqueue(job_id)
            return
        if outcome is FaultOutcome.FAILURE:
            updated = complete_terminal_failure(claimed, reason="injected failure")
            await self.jobs.save(updated)
            await self.jobs.record_attempt(
                JobAttempt(
                    job_id=claimed.job_id,
                    attempt_number=claimed.attempt_count,
                    outcome="failure",
                    detail="injected failure",
                )
            )
            await self.queue.acknowledge(job_id)
            return

        slot = await self.jobs.acquire_inference_slot(
            slot_count=self.settings.inference_max_concurrency
        )
        if slot is None:
            updated = complete_retryable_failure(
                claimed, reason="inference capacity exhausted"
            )
            await self.jobs.save(updated)
            await self.queue.acknowledge(job_id)
            if updated.status is JobStatus.RETRY:
                await self.queue.enqueue(job_id)
            return

        try:
            digest = claimed.content_sha256 or "unknown"
            await self.storage.get_bytes(claimed.object_key)
            result = await self.inference.extract(
                job_id=str(claimed.job_id),
                document_sha256=digest,
            )
            updated = complete_success(claimed, summary=result.summary)
            await self.jobs.save(updated)
            await self.jobs.record_attempt(
                JobAttempt(
                    job_id=claimed.job_id,
                    attempt_number=claimed.attempt_count,
                    outcome="succeeded",
                )
            )
            await self.queue.acknowledge(job_id)
        except InferenceError as exc:
            if exc.kind in {
                InferenceErrorKind.TIMEOUT,
                InferenceErrorKind.RATE_LIMIT,
                InferenceErrorKind.TRANSIENT,
            }:
                updated = complete_retryable_failure(claimed, reason=str(exc))
            else:
                updated = complete_terminal_failure(claimed, reason=str(exc))
            await self.jobs.save(updated)
            await self.jobs.record_attempt(
                JobAttempt(
                    job_id=claimed.job_id,
                    attempt_number=claimed.attempt_count,
                    outcome=exc.kind.value,
                    detail=str(exc),
                )
            )
            await self.queue.acknowledge(job_id)
            if updated.status is JobStatus.RETRY:
                await self.queue.enqueue(job_id)
        finally:
            await self.jobs.release_inference_slot(slot)

    async def _reconcile_loop(self) -> None:
        while not self._stopping:
            await self.reconcile_once()
            await asyncio.sleep(self.settings.reconcile_interval_seconds)

    async def reconcile_once(self) -> int:
        """Re-enqueue accepted/retry jobs missing from the wake transport."""

        candidates = await self.jobs.list_reconcile_candidates(
            limit=self.settings.reconcile_batch_size
        )
        requeued = 0
        for job in candidates:
            if job.status not in CLAIMABLE:
                continue
            if await self.queue.requeue_if_missing(job.job_id):
                requeued += 1
        return requeued


def build_worker(settings: Settings | None = None) -> Worker:
    """Construct a worker with cloud adapters when configured, else local fakes."""

    resolved = settings or Settings()
    stack = build_runtime_stack(resolved)
    return Worker(
        settings=resolved,
        jobs=stack.jobs,
        queue=stack.queue,
        storage=stack.storage,
        inference=stack.inference,
        policy=stack.policy,
    )


async def _run_worker() -> None:
    """Ensure schema exists when using PostgreSQL, then process jobs."""

    settings = Settings()
    stack = build_runtime_stack(settings)
    if stack.engine is not None:
        await create_schema(stack.engine)
    worker = Worker(
        settings=settings,
        jobs=stack.jobs,
        queue=stack.queue,
        storage=stack.storage,
        inference=stack.inference,
        policy=stack.policy,
    )
    try:
        await worker.run_forever()
    finally:
        if stack.engine is not None:
            await stack.engine.dispose()


def main() -> None:  # pragma: no cover
    """Run the worker until signalled."""

    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run_worker())


if __name__ == "__main__":
    main()
