# SPDX-License-Identifier: MIT
"""In-memory storage contract tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from halcyon_sim.storage import InMemoryObjectStorage, object_key_for


@pytest.mark.asyncio
async def test_put_get_delete_and_presign() -> None:
    storage = InMemoryObjectStorage()
    vendor_id = uuid4()
    job_id = uuid4()
    stored = await storage.put_pdf(
        vendor_id=vendor_id,
        job_id=job_id,
        content=b"%PDF-1.4\n%EOF",
        content_sha256="abc",
    )
    assert stored.key == object_key_for(vendor_id, job_id)
    assert await storage.get_bytes(stored.key) == b"%PDF-1.4\n%EOF"
    url = await storage.create_presigned_get(
        key=stored.key,
        vendor_id=vendor_id,
        ttl_seconds=60,
    )
    assert "ttl=60" in url
    with pytest.raises(PermissionError):
        await storage.create_presigned_get(
            key=stored.key,
            vendor_id=uuid4(),
            ttl_seconds=60,
        )
    await storage.delete(stored.key)
    with pytest.raises(FileNotFoundError):
        await storage.get_bytes(stored.key)
