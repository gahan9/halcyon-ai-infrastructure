# SPDX-License-Identifier: MIT
"""SQLAlchemy async adapter for the job ledger.

Kept beside the pure state machine in ``jobs.py`` so the domain module stays
readable while still shipping one PostgreSQL implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from halcyon_sim.jobs import (
    CLAIMABLE,
    DEFAULT_INFERENCE_MAX_CONCURRENCY,
    DEFAULT_LEASE_SECONDS,
    JobAttempt,
    JobRecord,
    JobStatus,
    claim_job,
    release_expired_lease,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    metadata = MetaData()


class JobRow(Base):
    """jobs table."""

    __tablename__ = "jobs"

    job_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    idempotency_key: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True
    )
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class JobAttemptRow(Base):
    """Immutable job_attempts table."""

    __tablename__ = "job_attempts"
    __table_args__ = (UniqueConstraint("job_id", "attempt_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


def _to_record(row: JobRow) -> JobRecord:
    return JobRecord(
        vendor_id=row.vendor_id,
        job_id=row.job_id,
        object_key=row.object_key,
        status=JobStatus(row.status),
        attempt_count=row.attempt_count,
        max_retries=row.max_retries,
        idempotency_key=row.idempotency_key,
        lease_owner=row.lease_owner,
        lease_expires_at=row.lease_expires_at,
        result_summary=row.result_summary,
        original_filename=row.original_filename,
        content_sha256=row.content_sha256,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _apply_record(row: JobRow, job: JobRecord) -> None:
    row.vendor_id = job.vendor_id
    row.object_key = job.object_key
    row.status = job.status.value
    row.attempt_count = job.attempt_count
    row.max_retries = job.max_retries
    row.idempotency_key = job.idempotency_key
    row.lease_owner = job.lease_owner
    row.lease_expires_at = job.lease_expires_at
    row.result_summary = job.result_summary
    row.original_filename = job.original_filename
    row.content_sha256 = job.content_sha256
    row.created_at = job.created_at
    row.updated_at = job.updated_at


class SqlAlchemyJobRepository:
    """Async PostgreSQL job ledger."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def insert(self, job: JobRecord) -> JobRecord:
        async with self._session_factory() as session:
            row = JobRow(
                job_id=job.job_id,
                vendor_id=job.vendor_id,
                object_key=job.object_key,
                status=job.status.value,
                attempt_count=job.attempt_count,
                max_retries=job.max_retries,
                idempotency_key=job.idempotency_key,
                lease_owner=job.lease_owner,
                lease_expires_at=job.lease_expires_at,
                result_summary=job.result_summary,
                original_filename=job.original_filename,
                content_sha256=job.content_sha256,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
            session.add(row)
            await session.commit()
            return job

    async def get(self, vendor_id: UUID, job_id: UUID) -> JobRecord | None:
        async with self._session_factory() as session:
            row = await session.get(JobRow, job_id)
            if row is None or row.vendor_id != vendor_id:
                return None
            return _to_record(row)

    async def get_by_id(self, job_id: UUID) -> JobRecord | None:
        async with self._session_factory() as session:
            row = await session.get(JobRow, job_id)
            return None if row is None else _to_record(row)

    async def save(self, job: JobRecord) -> JobRecord:
        async with self._session_factory() as session:
            row = await session.get(JobRow, job.job_id)
            if row is None:
                msg = f"job {job.job_id} not found"
                raise KeyError(msg)
            _apply_record(row, job)
            await session.commit()
            return job

    async def claim(
        self,
        job_id: UUID,
        *,
        owner: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> JobRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(JobRow)
                .where(JobRow.job_id == job_id)
                .where(JobRow.status.in_([s.value for s in CLAIMABLE]))
                .with_for_update()
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            claimed = claim_job(
                _to_record(row), owner=owner, lease_seconds=lease_seconds
            )
            _apply_record(row, claimed)
            await session.commit()
            return claimed

    async def record_attempt(self, attempt: JobAttempt) -> None:
        async with self._session_factory() as session:
            session.add(
                JobAttemptRow(
                    job_id=attempt.job_id,
                    attempt_number=attempt.attempt_number,
                    outcome=attempt.outcome,
                    detail=attempt.detail,
                    created_at=attempt.created_at,
                )
            )
            await session.commit()

    async def list_reconcile_candidates(self, *, limit: int) -> list[JobRecord]:
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            expired = await session.execute(
                select(JobRow)
                .where(JobRow.status == JobStatus.RUNNING.value)
                .where(JobRow.lease_expires_at.is_not(None))
                .where(JobRow.lease_expires_at <= now)
                .limit(limit)
                .with_for_update()
            )
            for row in expired.scalars():
                released = release_expired_lease(_to_record(row), now=now)
                _apply_record(row, released)
            await session.commit()

            result = await session.execute(
                select(JobRow)
                .where(JobRow.status.in_([s.value for s in CLAIMABLE]))
                .order_by(JobRow.updated_at.asc())
                .limit(limit)
            )
            return [_to_record(row) for row in result.scalars()]

    async def acquire_inference_slot(
        self,
        *,
        slot_count: int = DEFAULT_INFERENCE_MAX_CONCURRENCY,
    ) -> int | None:
        # Namespace locks under a fixed keyspace so replicas share the cap.
        async with self._session_factory() as session:
            for slot in range(slot_count):
                locked = await session.scalar(
                    text("SELECT pg_try_advisory_lock(:k)"),
                    {"k": 10_000 + slot},
                )
                if locked:
                    await session.commit()
                    return slot
            return None

    async def release_inference_slot(self, slot: int) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text("SELECT pg_advisory_unlock(:k)"),
                {"k": 10_000 + slot},
            )
            await session.commit()


def create_engine(database_url: str) -> AsyncEngine:
    """Create an async SQLAlchemy engine from a PostgreSQL URL."""

    url = database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # asyncpg rejects libpq sslmode=; DigitalOcean URIs use sslmode=require.
    url = url.replace("sslmode=require", "ssl=require")
    return create_async_engine(url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory for the job repository."""

    return async_sessionmaker(engine, expire_on_commit=False)


async def create_schema(engine: AsyncEngine) -> None:
    """Create tables for local/integration use (expand/contract migrations later)."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Silence unused import warnings for update helper reserved for future expand/contract.
_ = (Any, update)
