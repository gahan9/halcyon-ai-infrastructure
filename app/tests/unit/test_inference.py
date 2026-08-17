# SPDX-License-Identifier: MIT
"""Inference gateway classification tests."""

from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr

from halcyon_sim.config import InferenceCredentials
from halcyon_sim.faults import FaultPolicy
from halcyon_sim.inference import (
    FakeInferenceClient,
    HttpxInferenceClient,
    InferenceError,
    InferenceErrorKind,
)


@pytest.mark.asyncio
async def test_fake_inference_success() -> None:
    client = FakeInferenceClient(policy=FaultPolicy(seed=0))
    result = await client.extract(job_id="j1", document_sha256="abcd1234ffff")
    assert result.summary.startswith("extracted:")


@pytest.mark.asyncio
async def test_httpx_timeout_classified() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    transport = httpx.MockTransport(handler)
    client = HttpxInferenceClient(
        base_url="https://inference.example",
        model="m",
        credentials=InferenceCredentials(
            schema_version=1,
            environment="local",
            api_key=SecretStr("token"),
        ),
        timeout_seconds=1.0,
        transport=transport,
    )
    with pytest.raises(InferenceError) as exc:
        await client.extract(job_id="j1", document_sha256="abc")
    assert exc.value.kind is InferenceErrorKind.TIMEOUT
    await client.aclose()


@pytest.mark.asyncio
async def test_httpx_rate_limit_classified() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, request=request)

    transport = httpx.MockTransport(handler)
    client = HttpxInferenceClient(
        base_url="https://inference.example",
        model="m",
        credentials=InferenceCredentials(
            schema_version=1,
            environment="local",
            api_key=SecretStr("token"),
        ),
        timeout_seconds=1.0,
        transport=transport,
    )
    with pytest.raises(InferenceError) as exc:
        await client.extract(job_id="j1", document_sha256="abc")
    assert exc.value.kind is InferenceErrorKind.RATE_LIMIT
    await client.aclose()


@pytest.mark.asyncio
async def test_httpx_success_parses_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": " ok "}}]},
            request=request,
        )

    transport = httpx.MockTransport(handler)
    client = HttpxInferenceClient(
        base_url="https://inference.example",
        model="m",
        credentials=InferenceCredentials(
            schema_version=1,
            environment="local",
            api_key=SecretStr("token"),
        ),
        timeout_seconds=1.0,
        transport=transport,
    )
    result = await client.extract(job_id="j1", document_sha256="abc")
    assert result.summary == "ok"
    await client.aclose()
