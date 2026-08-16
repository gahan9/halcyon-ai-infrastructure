# SPDX-License-Identifier: MIT
"""Queue wake/ack semantics."""

from __future__ import annotations

from uuid import uuid4

import pytest

from halcyon_sim.queue import InMemoryJobQueue


@pytest.mark.asyncio
async def test_enqueue_pop_ack() -> None:
    queue = InMemoryJobQueue()
    job_id = uuid4()
    await queue.enqueue(job_id)
    assert await queue.requeue_if_missing(job_id) is False
    woken = await queue.pop_wake()
    assert woken == job_id
    await queue.acknowledge(job_id)
    assert await queue.requeue_if_missing(job_id) is True
