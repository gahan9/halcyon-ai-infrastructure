# SPDX-License-Identifier: MIT
"""Builder validation tests for adapters."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import SecretStr

from halcyon_sim.config import Settings
from halcyon_sim.inference import FakeInferenceClient, build_inference_client
from halcyon_sim.jobs import InMemoryJobRepository
from halcyon_sim.queue import InMemoryJobQueue, build_job_queue
from halcyon_sim.runtime import build_runtime_stack, cloud_backends_requested
from halcyon_sim.storage import InMemoryObjectStorage, build_object_storage


def test_build_object_storage_requires_settings() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        build_object_storage(Settings(_env_file=None))


def test_build_object_storage_rejects_bad_endpoint() -> None:
    settings = Settings(
        _env_file=None,
        spaces_endpoint="not-a-url",
        spaces_bucket="b",
        spaces_region="nyc3",
        spaces_credentials_json=SecretStr(
            json.dumps(
                {
                    "schema_version": 1,
                    "environment": "local",
                    "access_key": "k",
                    "secret_key": "s",
                }
            )
        ),
    )
    with pytest.raises(ValueError, match="http"):
        build_object_storage(settings)


def test_build_job_queue_requires_url() -> None:
    with pytest.raises(ValueError, match="VALKEY_URL"):
        build_job_queue(Settings(_env_file=None))


def test_build_job_queue_checks_idle_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_from_url(url: str, **kwargs: Any) -> object:
        captured["url"] = url
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("halcyon_sim.queue.Redis.from_url", fake_from_url)
    build_job_queue(
        Settings(_env_file=None, valkey_url=SecretStr("valkey://localhost:6379"))
    )

    retry = captured.pop("retry")
    assert retry.__class__.__name__ == "Retry"
    assert retry._retries == 3
    assert captured == {
        "url": "valkey://localhost:6379",
        "decode_responses": False,
        "health_check_interval": 30,
        "socket_connect_timeout": 5,
        "socket_keepalive": True,
        "socket_timeout": 10,
    }


def test_build_inference_client_local_fake() -> None:
    client = build_inference_client(Settings(_env_file=None))
    assert isinstance(client, FakeInferenceClient)


def test_build_runtime_stack_defaults_to_memory() -> None:
    stack = build_runtime_stack(Settings(_env_file=None))
    assert isinstance(stack.jobs, InMemoryJobRepository)
    assert isinstance(stack.queue, InMemoryJobQueue)
    assert isinstance(stack.storage, InMemoryObjectStorage)
    assert stack.engine is None
    assert cloud_backends_requested(Settings(_env_file=None)) is False


def test_build_runtime_stack_rejects_partial_cloud() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL and VALKEY_URL"):
        build_runtime_stack(
            Settings(_env_file=None, database_url=SecretStr("postgresql://x"))
        )
