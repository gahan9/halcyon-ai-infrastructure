# SPDX-License-Identifier: MIT
"""Offline integration markers (skip without credentials)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


def test_live_adapters_skipped_without_credentials() -> None:
    """Placeholder: live PG/Valkey/Spaces tests stay out of blocking CI."""

    if not os.getenv("HALCYON_INTEGRATION"):
        pytest.skip("HALCYON_INTEGRATION not set")
    pytest.fail("live integration harness not authorized without spend approval")
