# SPDX-License-Identifier: MIT
"""Unit tests for auth adapters."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from halcyon_sim.auth import (
    FailClosedAuthProvider,
    FakeAuthProvider,
    build_auth_provider,
)
from halcyon_sim.config import AppEnvironment, AuthMode, Settings


@pytest.mark.asyncio
async def test_fake_auth_derives_stable_vendor_id() -> None:
    provider = FakeAuthProvider(app_env=AppEnvironment.LOCAL)
    first = await provider.authenticate("Bearer vendor-a")
    second = await provider.authenticate("Bearer vendor-a")
    other = await provider.authenticate("Bearer vendor-b")
    assert first.vendor_id == second.vendor_id
    assert first.vendor_id != other.vendor_id


def test_fake_auth_blocked_outside_local() -> None:
    with pytest.raises(RuntimeError):
        FakeAuthProvider(app_env=AppEnvironment.STAGING)


@pytest.mark.asyncio
async def test_fail_closed_auth_unavailable() -> None:
    provider = FailClosedAuthProvider()
    with pytest.raises(HTTPException) as exc:
        await provider.authenticate("Bearer anything")
    assert exc.value.status_code == 503


def test_build_auth_provider_respects_mode() -> None:
    local = Settings(_env_file=None, auth_mode=AuthMode.LOCAL)
    assert isinstance(build_auth_provider(local), FakeAuthProvider)
    closed = Settings(
        _env_file=None,
        app_env=AppEnvironment.STAGING,
        auth_mode=AuthMode.FAIL_CLOSED,
    )
    assert isinstance(build_auth_provider(closed), FailClosedAuthProvider)
