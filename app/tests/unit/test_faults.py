# SPDX-License-Identifier: MIT
"""Unit tests for deterministic fault policy."""

from __future__ import annotations

import pytest

from halcyon_sim.faults import FaultOutcome, FaultPolicy


def test_fault_policy_rejects_negative_rates() -> None:
    with pytest.raises(ValueError):
        FaultPolicy(timeout_rate=-0.1)


def test_fault_policy_rejects_rates_above_one() -> None:
    with pytest.raises(ValueError):
        FaultPolicy(timeout_rate=0.6, failure_rate=0.5)


def test_fault_policy_zero_rates_always_success() -> None:
    policy = FaultPolicy(seed=7)
    assert policy.choose("job-a") is FaultOutcome.SUCCESS
    assert policy.choose("job-b") is FaultOutcome.SUCCESS


def test_fault_policy_is_deterministic_for_same_seed_and_job() -> None:
    policy = FaultPolicy(seed=42, timeout_rate=0.4, failure_rate=0.4)
    first = [policy.choose(f"job-{i}") for i in range(20)]
    second = [policy.choose(f"job-{i}") for i in range(20)]
    assert first == second
    assert FaultOutcome.TIMEOUT in first or FaultOutcome.FAILURE in first


def test_work_seconds_stays_in_window() -> None:
    policy = FaultPolicy(seed=3)
    value = policy.work_seconds("job-1", 20.0, 240.0)
    assert 20.0 <= value <= 240.0
