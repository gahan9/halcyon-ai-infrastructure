# SPDX-License-Identifier: MIT
"""Deterministic injected outcomes for tests and staging."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from random import Random


class FaultOutcome(StrEnum):
    """Possible injected inference outcomes."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class FaultPolicy:
    """Seeded fault selector. Rates must sum to at most 1.0."""

    seed: int = 0
    timeout_rate: float = 0.0
    failure_rate: float = 0.0

    def __post_init__(self) -> None:
        if self.timeout_rate < 0.0 or self.failure_rate < 0.0:
            msg = "fault rates must be non-negative"
            raise ValueError(msg)
        if self.timeout_rate + self.failure_rate > 1.0:
            msg = "timeout_rate + failure_rate must be <= 1.0"
            raise ValueError(msg)

    def choose(self, job_id: str) -> FaultOutcome:
        """Return a deterministic outcome for ``job_id`` under this seed."""

        rng = Random(f"{self.seed}:{job_id}")
        draw = rng.random()
        if draw < self.timeout_rate:
            return FaultOutcome.TIMEOUT
        if draw < self.timeout_rate + self.failure_rate:
            return FaultOutcome.FAILURE
        return FaultOutcome.SUCCESS

    def work_seconds(self, job_id: str, minimum: float, maximum: float) -> float:
        """Return a deterministic simulated work duration in ``[minimum, maximum]``."""

        if minimum < 0 or maximum < minimum:
            msg = "work window must satisfy 0 <= minimum <= maximum"
            raise ValueError(msg)
        rng = Random(f"{self.seed}:work:{job_id}")
        return rng.uniform(minimum, maximum)
