# SPDX-License-Identifier: MIT
"""Single OpenAI-compatible async inference gateway."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

import httpx

from halcyon_sim.config import InferenceCredentials, Settings
from halcyon_sim.faults import FaultOutcome, FaultPolicy


class InferenceErrorKind(StrEnum):
    """Classified inference failures."""

    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    TRANSIENT = "transient"
    TERMINAL = "terminal"


class InferenceError(Exception):
    """Typed inference failure."""

    def __init__(self, kind: InferenceErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Normalized model response."""

    summary: str
    model: str


class InferenceClient(Protocol):
    """Worker-facing inference port."""

    async def extract(self, *, job_id: str, document_sha256: str) -> InferenceResult:
        """Run a bounded inference call for the job."""


class FakeInferenceClient:
    """Deterministic client driven by a fault policy."""

    def __init__(
        self,
        *,
        policy: FaultPolicy,
        model: str = "fake-model",
        timeout_seconds: float = 240.0,
    ) -> None:
        self._policy = policy
        self._model = model
        self._timeout_seconds = timeout_seconds

    async def extract(self, *, job_id: str, document_sha256: str) -> InferenceResult:
        outcome = self._policy.choose(job_id)
        if outcome is FaultOutcome.TIMEOUT:
            raise InferenceError(InferenceErrorKind.TIMEOUT, "injected timeout")
        if outcome is FaultOutcome.FAILURE:
            raise InferenceError(InferenceErrorKind.TERMINAL, "injected failure")
        return InferenceResult(
            summary=f"extracted:{document_sha256[:12]}",
            model=self._model,
        )


class HttpxInferenceClient:
    """DigitalOcean Serverless Inference via OpenAI-compatible chat completions."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        credentials: InferenceCredentials,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._model = model
        self._api_key = credentials.api_key
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def extract(self, *, job_id: str, document_sha256: str) -> InferenceResult:
        headers = {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Summarize contract extraction for simulation job "
                        f"{job_id} with digest {document_sha256}."
                    ),
                }
            ],
        }
        try:
            response = await self._client.post(
                "/v1/chat/completions",
                headers=headers,
                json=body,
            )
        except httpx.TimeoutException as exc:
            raise InferenceError(
                InferenceErrorKind.TIMEOUT, "inference timed out"
            ) from exc
        except httpx.HTTPError as exc:
            raise InferenceError(
                InferenceErrorKind.TRANSIENT, "inference transport error"
            ) from exc

        if response.status_code == 429:
            raise InferenceError(InferenceErrorKind.RATE_LIMIT, "rate limited")
        if response.status_code in {401, 403, 404}:
            raise InferenceError(
                InferenceErrorKind.TERMINAL, f"auth/model error {response.status_code}"
            )
        if response.status_code >= 500:
            raise InferenceError(
                InferenceErrorKind.TRANSIENT, f"provider error {response.status_code}"
            )
        if response.status_code >= 400:
            raise InferenceError(
                InferenceErrorKind.TERMINAL, f"client error {response.status_code}"
            )

        payload = response.json()
        try:
            summary = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise InferenceError(
                InferenceErrorKind.TERMINAL, "malformed response"
            ) from exc
        if not isinstance(summary, str) or not summary.strip():
            raise InferenceError(InferenceErrorKind.TERMINAL, "empty response")
        return InferenceResult(summary=summary.strip()[:2000], model=self._model)


def build_inference_client(
    settings: Settings,
    *,
    policy: FaultPolicy | None = None,
) -> InferenceClient:
    """Build the production httpx gateway or a policy-driven fake for local tests."""

    if settings.app_env.value == "local" and settings.llm_credentials_json is None:
        return FakeInferenceClient(
            policy=policy
            or FaultPolicy(
                seed=settings.simulation_seed,
                timeout_rate=settings.simulated_timeout_rate,
                failure_rate=settings.simulated_failure_rate,
            ),
            model=settings.llm_model,
            timeout_seconds=float(settings.inference_timeout_seconds),
        )
    return HttpxInferenceClient(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        credentials=settings.parse_inference_credentials(),
        timeout_seconds=float(settings.inference_timeout_seconds),
    )
