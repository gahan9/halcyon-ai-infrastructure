# SPDX-License-Identifier: MIT
"""Unit tests for settings and secret guards."""

from __future__ import annotations

import json

import pytest
from pydantic import SecretStr

from halcyon_sim.config import AuthMode, Settings


def _spaces_json(environment: str = "local") -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "environment": environment,
            "access_key": "SPACES_KEY_PLACEHOLDER",
            "secret_key": "SPACES_SECRET_PLACEHOLDER",
        }
    )


def _llm_json(environment: str = "local") -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "environment": environment,
            "api_key": "INFERENCE_TOKEN_PLACEHOLDER",
        }
    )


def test_settings_defaults_are_safe() -> None:
    settings = Settings(
        _env_file=None,
        spaces_credentials_json=SecretStr(_spaces_json()),
        llm_credentials_json=SecretStr(_llm_json()),
    )
    assert settings.app_env.value == "local"
    assert settings.simulated_timeout_rate == 0.0
    assert settings.inference_max_concurrency == 10
    assert settings.job_max_retries == 3


def test_production_rejects_nonzero_simulation_rates() -> None:
    with pytest.raises(ValueError, match="production rejects"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_mode=AuthMode.FAIL_CLOSED,
            simulated_timeout_rate=0.1,
            spaces_credentials_json=SecretStr(_spaces_json("production")),
            llm_credentials_json=SecretStr(_llm_json("production")),
        )


def test_production_rejects_local_auth() -> None:
    with pytest.raises(ValueError, match="local auth"):
        Settings(
            _env_file=None,
            app_env="prod",
            auth_mode=AuthMode.LOCAL,
            spaces_credentials_json=SecretStr(_spaces_json("prod")),
            llm_credentials_json=SecretStr(_llm_json("prod")),
        )


def test_secret_environment_mismatch_fails_closed() -> None:
    with pytest.raises(ValueError, match="does not match"):
        Settings(
            _env_file=None,
            app_env="staging",
            auth_mode=AuthMode.FAIL_CLOSED,
            spaces_credentials_json=SecretStr(_spaces_json("local")),
            llm_credentials_json=SecretStr(_llm_json("staging")),
        )


def test_secret_values_are_masked_in_repr() -> None:
    settings = Settings(
        _env_file=None,
        spaces_credentials_json=SecretStr(_spaces_json()),
        llm_credentials_json=SecretStr(_llm_json()),
    )
    text = repr(settings)
    assert "INFERENCE_TOKEN_PLACEHOLDER" not in text
    assert "SPACES_SECRET_PLACEHOLDER" not in text
    creds = settings.parse_inference_credentials()
    assert "INFERENCE_TOKEN_PLACEHOLDER" not in repr(creds)
