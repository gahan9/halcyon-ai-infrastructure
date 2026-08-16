# SPDX-License-Identifier: MIT
"""Unit tests for job state transitions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from halcyon_sim.jobs import (
    IllegalTransitionError,
    JobStatus,
    claim_job,
    complete_retryable_failure,
    complete_success,
    complete_terminal_failure,
    is_enqueueable,
    new_job,
    reject_quarantine,
    release_expired_lease,
    release_quarantine,
)


def test_new_job_accepted_when_scan_not_required() -> None:
    job = new_job(
        vendor_id=uuid4(),
        object_key="vendors/a/jobs/b/source.pdf",
        scan_required=False,
    )
    assert job.status is JobStatus.ACCEPTED
    assert is_enqueueable(job.status)


def test_new_job_quarantined_when_scan_required() -> None:
    job = new_job(
        vendor_id=uuid4(),
        object_key="vendors/a/jobs/b/source.pdf",
        scan_required=True,
    )
    assert job.status is JobStatus.QUARANTINED
    assert not is_enqueueable(job.status)


def test_quarantined_job_cannot_be_claimed() -> None:
    job = new_job(
        vendor_id=uuid4(),
        object_key="vendors/a/jobs/b/source.pdf",
        scan_required=True,
    )
    with pytest.raises(IllegalTransitionError):
        claim_job(job, owner="worker-1")


def test_claim_and_success_path() -> None:
    job = new_job(
        vendor_id=uuid4(),
        object_key="vendors/a/jobs/b/source.pdf",
        scan_required=False,
    )
    running = claim_job(job, owner="worker-1")
    assert running.status is JobStatus.RUNNING
    assert running.attempt_count == 1
    done = complete_success(running, summary="ok")
    assert done.status is JobStatus.SUCCEEDED


@pytest.mark.parametrize(
    ("attempts_before_fail", "expected"),
    [
        (1, JobStatus.RETRY),
        (2, JobStatus.RETRY),
        (3, JobStatus.RETRY),
        (4, JobStatus.DEAD_LETTER),
    ],
)
def test_retry_ceiling_is_initial_plus_three(
    attempts_before_fail: int,
    expected: JobStatus,
) -> None:
    job = new_job(
        vendor_id=uuid4(),
        object_key="vendors/a/jobs/b/source.pdf",
        scan_required=False,
        max_retries=3,
    )
    current = job
    for index in range(attempts_before_fail):
        current = claim_job(current, owner=f"worker-{index}")
        if index + 1 < attempts_before_fail:
            current = complete_retryable_failure(current, reason="timeout")
    final = complete_retryable_failure(current, reason="timeout")
    assert final.status is expected
    assert current.attempt_count == attempts_before_fail


def test_terminal_failure_dead_letters_without_retry() -> None:
    job = claim_job(
        new_job(
            vendor_id=uuid4(),
            object_key="vendors/a/jobs/b/source.pdf",
            scan_required=False,
        ),
        owner="worker-1",
    )
    dead = complete_terminal_failure(job, reason="auth error")
    assert dead.status is JobStatus.DEAD_LETTER


def test_scanner_release_and_reject() -> None:
    quarantined = new_job(
        vendor_id=uuid4(),
        object_key="vendors/a/jobs/b/source.pdf",
        scan_required=True,
    )
    accepted = release_quarantine(quarantined)
    assert accepted.status is JobStatus.ACCEPTED
    rejected = reject_quarantine(quarantined, reason="malware")
    assert rejected.status is JobStatus.REJECTED


def test_expired_lease_returns_to_retry() -> None:
    now = datetime.now(UTC)
    running = claim_job(
        new_job(
            vendor_id=uuid4(),
            object_key="vendors/a/jobs/b/source.pdf",
            scan_required=False,
        ),
        owner="worker-1",
        now=now - timedelta(seconds=10),
        lease_seconds=1,
    )
    retried = release_expired_lease(running, now=now)
    assert retried.status is JobStatus.RETRY
    assert retried.lease_owner is None
