# SPDX-License-Identifier: MIT
"""FastAPI transport: upload and vendor-scoped status only."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import uvicorn
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from halcyon_sim.auth import AuthProvider, Principal, build_auth_provider
from halcyon_sim.config import Settings
from halcyon_sim.jobs import (
    JobRepository,
    JobStatus,
    is_enqueueable,
    new_job,
)
from halcyon_sim.jobs_sql import create_schema
from halcyon_sim.pdf_validate import (
    UploadValidationError,
    sanitize_filename,
    validate_pdf_bytes,
)
from halcyon_sim.queue import JobQueue
from halcyon_sim.runtime import RuntimeStack, build_runtime_stack
from halcyon_sim.storage import ObjectStorage

logger = logging.getLogger(__name__)


class JobStatusResponse(BaseModel):
    """Vendor-scoped job status payload."""

    job_id: UUID
    status: JobStatus
    attempt_count: int
    result_summary: str | None = None


class UploadAcceptedResponse(BaseModel):
    """202 response body."""

    job_id: UUID
    status: JobStatus


class AppState:
    """Process-local wired dependencies."""

    def __init__(
        self,
        *,
        settings: Settings,
        auth: AuthProvider,
        jobs: JobRepository,
        queue: JobQueue,
        storage: ObjectStorage,
    ) -> None:
        self.settings = settings
        self.auth = auth
        self.jobs = jobs
        self.queue = queue
        self.storage = storage


def create_app(
    *,
    settings: Settings | None = None,
    auth: AuthProvider | None = None,
    jobs: JobRepository | None = None,
    queue: JobQueue | None = None,
    storage: ObjectStorage | None = None,
    stack: RuntimeStack | None = None,
) -> FastAPI:
    """Build the FastAPI application with injectable collaborators."""

    resolved_settings = settings or Settings()
    if jobs is not None and queue is not None and storage is not None:
        resolved_jobs = jobs
        resolved_queue = queue
        resolved_storage = storage
        engine = None if stack is None else stack.engine
    else:
        resolved_stack = stack or build_runtime_stack(resolved_settings)
        resolved_jobs = jobs or resolved_stack.jobs
        resolved_queue = queue or resolved_stack.queue
        resolved_storage = storage or resolved_stack.storage
        engine = resolved_stack.engine
    state = AppState(
        settings=resolved_settings,
        auth=auth or build_auth_provider(resolved_settings),
        jobs=resolved_jobs,
        queue=resolved_queue,
        storage=resolved_storage,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if engine is not None:
            await create_schema(engine)
        yield
        if engine is not None:
            await engine.dispose()

    app = FastAPI(title="halcyon-sim", version="0.1.0", lifespan=lifespan)
    app.state.halcyon = state

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    async def current_principal(
        authorization: str | None = Header(default=None),
    ) -> Principal:
        return await state.auth.authenticate(authorization)

    @app.post("/v1/contracts", status_code=status.HTTP_202_ACCEPTED)
    async def upload_contract(
        file: UploadFile = File(...),
        principal: Principal = Depends(current_principal),
    ) -> UploadAcceptedResponse:
        raw = await file.read(state.settings.upload_max_bytes + 1)
        try:
            validated = validate_pdf_bytes(
                raw,
                max_bytes=state.settings.upload_max_bytes,
                content_type=file.content_type,
            )
        except UploadValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        job_id = uuid4()
        filename = sanitize_filename(file.filename)
        stored = await state.storage.put_pdf(
            vendor_id=principal.vendor_id,
            job_id=job_id,
            content=validated.content,
            content_sha256=validated.sha256,
        )
        job = new_job(
            vendor_id=principal.vendor_id,
            object_key=stored.key,
            scan_required=state.settings.upload_scan_required,
            original_filename=filename,
            content_sha256=validated.sha256,
            max_retries=state.settings.job_max_retries,
            job_id=job_id,
        )
        try:
            await state.jobs.insert(job)
        except Exception:
            try:
                await state.storage.delete(stored.key)
            except Exception:
                logger.exception("compensating delete failed for orphan object")
            raise

        if is_enqueueable(job.status):
            await state.queue.enqueue(job.job_id)

        return UploadAcceptedResponse(job_id=job.job_id, status=job.status)

    @app.get("/v1/contracts/{job_id}")
    async def get_status(
        job_id: UUID,
        principal: Principal = Depends(current_principal),
    ) -> JobStatusResponse:
        job = await state.jobs.get(principal.vendor_id, job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="job not found"
            )
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            attempt_count=job.attempt_count,
            result_summary=job.result_summary,
        )

    @app.post("/v1/contracts/{job_id}/presign")
    async def presign(
        job_id: UUID,
        principal: Principal = Depends(current_principal),
        ttl_seconds: int | None = None,
    ) -> JSONResponse:
        job = await state.jobs.get(principal.vendor_id, job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="job not found"
            )
        ttl = ttl_seconds or state.settings.presigned_url_ttl_seconds
        if ttl > state.settings.presigned_url_max_ttl_seconds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="ttl too large"
            )
        try:
            url = await state.storage.create_presigned_get(
                key=job.object_key,
                vendor_id=principal.vendor_id,
                ttl_seconds=ttl,
            )
        except PermissionError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="denied"
            ) from exc
        # Do not log the URL.
        return JSONResponse({"job_id": str(job_id), "expires_in": ttl, "url": url})

    return app


class _CliSettings(BaseModel):
    """Tiny helper for module docstring completeness."""

    port: int = Field(default=8080)


def main() -> None:  # pragma: no cover
    """Run the API with uvicorn."""

    settings = Settings()
    app = create_app(settings=settings)
    uvicorn.run(
        app,
        host="0.0.0.0",  # nosec B104 - App Platform health checks need all interfaces
        port=settings.app_port,
        log_level=settings.app_log_level.lower(),
    )


if __name__ == "__main__":
    main()
