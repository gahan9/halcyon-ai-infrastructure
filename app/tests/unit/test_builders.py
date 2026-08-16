# SPDX-License-Identifier: MIT
"""Builder validation tests for adapters."""

from __future__ import annotations

import json

import pytest
from pydantic import SecretStr

from halcyon_sim.config import Settings
from halcyon_sim.inference import FakeInferenceClient, build_inference_client
from halcyon_sim.queue import build_job_queue
from halcyon_sim.storage import build_object_storage


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


def test_build_inference_client_local_fake() -> None:
    client = build_inference_client(Settings(_env_file=None))
    assert isinstance(client, FakeInferenceClient)
