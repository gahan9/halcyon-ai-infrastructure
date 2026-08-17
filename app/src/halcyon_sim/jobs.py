# SPDX-License-Identifier: MIT
"""Job state machine and ledger contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Final, Protocol
from uuid import UUID, uuid4


class JobStatus(StrEnum):
    """Authoritative PostgreSQL job states."""

    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"
    RUNNING = "running"
    RETRY = "retry"
    SUCCEEDED = "succeeded"
    DEAD_LETTER = "dead_letter"
    REJECTED = "rejected"


CLAIMABLE: Final[frozenset[JobStatus]] = frozenset(
    {JobStatus.ACCEPTED, JobStatus.RETRY}
)
TERMINAL: Final[frozenset[JobStatus]] = frozenset(
    {JobStatus.SUCCEEDED, JobStatus.DEAD_LETTER, JobStatus.REJECTED}
)

# Initial attempt plus JOB_MAX_RETRIES retries.
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_LEASE_SECONDS: Final[int] = 570
DEFAULT_INFERENCE_MAX_CONCURRENCY: Final[int] = 10


class IllegalTransitionError(ValueError):
    """Raised when a state transition is not permitted."""


@dataclass(frozen=True, slots=True)
class JobRecord:
    """In-memory representation of a durable job row."""

    vendor_id: UUID
    job_id: UUID
    object_key: str
    status: JobStatus
    attempt_count: int = 0
    max_retries: int = DEFAULT_MAX_RETRIES
    idempotency_key: str = ""
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    result_summary: str | None = None
    original_filename: str | None = None
    content_sha256: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def max_attempts(self) -> int:
        """Total attempts allowed: initial plus retries."""

        return self.max_retries + 1

    @property
    def attempts_remaining(self) -> int:
        """Attempts left before dead-letter."""

        return max(self.max_attempts - self.attempt_count, 0)


def new_job(
    *,
    vendor_id: UUID,
    object_key: str,
    scan_required: bool,
    original_filename: str | None = None,
    content_sha256: str | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    job_id: UUID | None = None,
) -> JobRecord:
    """Create a new job in ``accepted`` or ``quarantined``."""

    resolved_id = job_id or uuid4()
    status = JobStatus.QUARANTINED if scan_required else JobStatus.ACCEPTED
    return JobRecord(
        vendor_id=vendor_id,
        job_id=resolved_id,
        object_key=object_key,
        status=status,
        max_retries=max_retries,
        idempotency_key=f"{vendor_id}:{resolved_id}",
        original_filename=original_filename,
        content_sha256=content_sha256,
    )


def assert_transition(current: JobStatus, target: JobStatus) -> None:
    """Raise if ``current`` may not move to ``target``."""

    allowed: dict[JobStatus, frozenset[JobStatus]] = {
        JobStatus.QUARANTINED: frozenset({JobStatus.ACCEPTED, JobStatus.REJECTED}),
        JobStatus.ACCEPTED: frozenset({JobStatus.RUNNING}),
        JobStatus.RETRY: frozenset({JobStatus.RUNNING}),
        JobStatus.RUNNING: frozenset(
            {JobStatus.SUCCEEDED, JobStatus.RETRY, JobStatus.DEAD_LETTER}
        ),
        JobStatus.SUCCEEDED: frozenset(),
        JobStatus.DEAD_LETTER: frozenset(),
        JobStatus.REJECTED: frozenset(),
    }
    if target not in allowed[current]:
        msg = f"illegal transition {current} -> {target}"
        raise IllegalTransitionError(msg)


def claim_job(
    job: JobRecord,
    *,
    owner: str,
    now: datetime | None = None,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
) -> JobRecord:
    """Atomically-shaped claim of an ``accepted``/``retry`` job."""

    if job.status not in CLAIMABLE:
        msg = f"job {job.job_id} status {job.status} is not claimable"
        raise IllegalTransitionError(msg)
    assert_transition(job.status, JobStatus.RUNNING)
    moment = now or datetime.now(UTC)
    return JobRecord(
        vendor_id=job.vendor_id,
        job_id=job.job_id,
        object_key=job.object_key,
        status=JobStatus.RUNNING,
        attempt_count=job.attempt_count + 1,
        max_retries=job.max_retries,
        idempotency_key=job.idempotency_key,
        lease_owner=owner,
        lease_expires_at=moment + timedelta(seconds=lease_seconds),
        result_summary=job.result_summary,
        original_filename=job.original_filename,
        content_sha256=job.content_sha256,
        created_at=job.created_at,
        updated_at=moment,
    )


def complete_success(job: JobRecord, *, summary: str) -> JobRecord:
    """Mark a running job succeeded."""

    assert_transition(job.status, JobStatus.SUCCEEDED)
    return _with_status(job, JobStatus.SUCCEEDED, result_summary=summary)


def complete_retryable_failure(job: JobRecord, *, reason: str) -> JobRecord:
    """Move running work to ``retry`` or ``dead_letter`` by attempt ceiling."""

    assert_transition(job.status, JobStatus.RETRY)
    if job.attempt_count >= job.max_attempts:
        return _with_status(
            job,
            JobStatus.DEAD_LETTER,
            result_summary=reason,
            clear_lease=True,
        )
    return _with_status(job, JobStatus.RETRY, result_summary=reason, clear_lease=True)


def complete_terminal_failure(job: JobRecord, *, reason: str) -> JobRecord:
    """Dead-letter a running job without consuming remaining retries."""

    assert_transition(job.status, JobStatus.DEAD_LETTER)
    return _with_status(
        job,
        JobStatus.DEAD_LETTER,
        result_summary=reason,
        clear_lease=True,
    )


def release_quarantine(job: JobRecord) -> JobRecord:
    """Scanner release path: quarantined -> accepted."""

    assert_transition(job.status, JobStatus.ACCEPTED)
    return _with_status(job, JobStatus.ACCEPTED, clear_lease=True)


def reject_quarantine(job: JobRecord, *, reason: str) -> JobRecord:
    """Scanner reject path."""

    assert_transition(job.status, JobStatus.REJECTED)
    return _with_status(
        job, JobStatus.REJECTED, result_summary=reason, clear_lease=True
    )


def release_expired_lease(job: JobRecord, *, now: datetime | None = None) -> JobRecord:
    """Return an expired running lease to ``retry`` or ``dead_letter``."""

    moment = now or datetime.now(UTC)
    if job.status != JobStatus.RUNNING:
        msg = f"job {job.job_id} is not running"
        raise IllegalTransitionError(msg)
    if job.lease_expires_at is None or job.lease_expires_at > moment:
        msg = f"job {job.job_id} lease is still active"
        raise IllegalTransitionError(msg)
    if job.attempt_count >= job.max_attempts:
        return _with_status(
            job,
            JobStatus.DEAD_LETTER,
            result_summary="lease expired with attempts exhausted",
            clear_lease=True,
            now=moment,
        )
    return _with_status(
        job,
        JobStatus.RETRY,
        result_summary="lease expired",
        clear_lease=True,
        now=moment,
    )


def is_enqueueable(status: JobStatus) -> bool:
    """Only accepted/retry jobs may be woken via Valkey."""

    return status in CLAIMABLE


def _with_status(
    job: JobRecord,
    status: JobStatus,
    *,
    result_summary: str | None = None,
    clear_lease: bool = False,
    now: datetime | None = None,
) -> JobRecord:
    moment = now or datetime.now(UTC)
    return JobRecord(
        vendor_id=job.vendor_id,
        job_id=job.job_id,
        object_key=job.object_key,
        status=status,
        attempt_count=job.attempt_count,
        max_retries=job.max_retries,
        idempotency_key=job.idempotency_key,
        lease_owner=None if clear_lease else job.lease_owner,
        lease_expires_at=None if clear_lease else job.lease_expires_at,
        result_summary=result_summary
        if result_summary is not None
        else job.result_summary,
        original_filename=job.original_filename,
        content_sha256=job.content_sha256,
        created_at=job.created_at,
        updated_at=moment,
    )


@dataclass(frozen=True, slots=True)
class JobAttempt:
    """Immutable attempt history row."""

    job_id: UUID
    attempt_number: int
    outcome: str
    detail: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class JobRepository(Protocol):
    """PostgreSQL-backed job ledger port."""

    async def insert(self, job: JobRecord) -> JobRecord:
        """Persist a new job row."""

    async def get(self, vendor_id: UUID, job_id: UUID) -> JobRecord | None:
        """Vendor-scoped job lookup."""

    async def get_by_id(self, job_id: UUID) -> JobRecord | None:
        """Internal lookup by job id."""

    async def save(self, job: JobRecord) -> JobRecord:
        """Persist a mutated job row with optimistic status checks where needed."""

    async def claim(
        self,
        job_id: UUID,
        *,
        owner: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> JobRecord | None:
        """Conditional claim of an accepted/retry job."""

    async def record_attempt(self, attempt: JobAttempt) -> None:
        """Append immutable attempt history."""

    async def list_reconcile_candidates(self, *, limit: int) -> list[JobRecord]:
        """Return accepted/retry jobs that are not currently leased."""

    async def acquire_inference_slot(
        self, *, slot_count: int = DEFAULT_INFERENCE_MAX_CONCURRENCY
    ) -> int | None:
        """Acquire one fleet-wide advisory-lock slot; None if exhausted."""

    async def release_inference_slot(self, slot: int) -> None:
        """Release a previously acquired inference slot."""


class InMemoryJobRepository:
    """Process-local ledger for unit and offline integration tests."""

    def __init__(
        self, *, inference_slots: int = DEFAULT_INFERENCE_MAX_CONCURRENCY
    ) -> None:
        self.jobs: dict[UUID, JobRecord] = {}
        self.attempts: list[JobAttempt] = []
        self._slots = set(range(inference_slots))
        self._held: dict[int, bool] = {}

    async def insert(self, job: JobRecord) -> JobRecord:
        if job.job_id in self.jobs:
            msg = f"duplicate job {job.job_id}"
            raise ValueError(msg)
        self.jobs[job.job_id] = job
        return job

    async def get(self, vendor_id: UUID, job_id: UUID) -> JobRecord | None:
        job = self.jobs.get(job_id)
        if job is None or job.vendor_id != vendor_id:
            return None
        return job

    async def get_by_id(self, job_id: UUID) -> JobRecord | None:
        return self.jobs.get(job_id)

    async def save(self, job: JobRecord) -> JobRecord:
        self.jobs[job.job_id] = job
        return job

    async def claim(
        self,
        job_id: UUID,
        *,
        owner: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> JobRecord | None:
        job = self.jobs.get(job_id)
        if job is None or job.status not in CLAIMABLE:
            return None
        claimed = claim_job(job, owner=owner, lease_seconds=lease_seconds)
        self.jobs[job_id] = claimed
        return claimed

    async def record_attempt(self, attempt: JobAttempt) -> None:
        self.attempts.append(attempt)

    async def list_reconcile_candidates(self, *, limit: int) -> list[JobRecord]:
        now = datetime.now(UTC)
        candidates: list[JobRecord] = []
        for job in self.jobs.values():
            if job.status in CLAIMABLE:
                candidates.append(job)
            elif (
                job.status is JobStatus.RUNNING
                and job.lease_expires_at is not None
                and job.lease_expires_at <= now
            ):
                released = release_expired_lease(job, now=now)
                self.jobs[job.job_id] = released
                if released.status in CLAIMABLE:
                    candidates.append(released)
            if len(candidates) >= limit:
                break
        return candidates[:limit]

    async def acquire_inference_slot(
        self,
        *,
        slot_count: int = DEFAULT_INFERENCE_MAX_CONCURRENCY,
    ) -> int | None:
        del slot_count
        for slot in sorted(self._slots):
            if not self._held.get(slot, False):
                self._held[slot] = True
                return slot
        return None

    async def release_inference_slot(self, slot: int) -> None:
        self._held[slot] = False
