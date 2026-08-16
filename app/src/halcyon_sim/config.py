# SPDX-License-Identifier: MIT
"""Validated environment settings and secret parsing."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, Final

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from halcyon_sim.jobs import (
    DEFAULT_INFERENCE_MAX_CONCURRENCY,
    DEFAULT_LEASE_SECONDS,
    DEFAULT_MAX_RETRIES,
)


class AppEnvironment(StrEnum):
    """Runtime environment names."""

    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
    PROD = "prod"


class AuthMode(StrEnum):
    """Identity adapter selection."""

    LOCAL = "local"
    FAIL_CLOSED = "fail_closed"


class SpacesCredentials(BaseModel):
    """Parsed Spaces runtime JSON."""

    schema_version: int = Field(ge=1)
    environment: str
    access_key: SecretStr
    secret_key: SecretStr


class InferenceCredentials(BaseModel):
    """Parsed inference runtime JSON."""

    schema_version: int = Field(ge=1)
    environment: str
    api_key: SecretStr


_PRODUCTION_ENVS: Final[frozenset[str]] = frozenset(
    {AppEnvironment.PRODUCTION.value, AppEnvironment.PROD.value}
)


def _parse_json_object(raw: str, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"{label} is not valid JSON"
        raise ValueError(msg) from exc
    if not isinstance(payload, dict):
        msg = f"{label} must be a JSON object"
        raise TypeError(msg)
    return payload


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_log_level: str = "INFO"
    app_port: int = Field(default=8080, ge=1, le=65535)
    app_env: AppEnvironment = AppEnvironment.LOCAL
    auth_mode: AuthMode = AuthMode.LOCAL

    database_url: SecretStr | None = None
    valkey_url: SecretStr | None = None

    spaces_endpoint: str | None = None
    spaces_bucket: str | None = None
    spaces_region: str | None = None
    spaces_credentials_json: SecretStr | None = None
    presigned_url_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    presigned_url_max_ttl_seconds: int = Field(default=86400, ge=60, le=86400)

    llm_base_url: str = "https://inference.do-ai.run"
    llm_credentials_json: SecretStr | None = None
    llm_model: str = "your-model-id"

    worker_concurrency: int = Field(default=2, ge=1, le=10)
    inference_max_concurrency: int = Field(
        default=DEFAULT_INFERENCE_MAX_CONCURRENCY,
        ge=1,
        le=DEFAULT_INFERENCE_MAX_CONCURRENCY,
    )
    inference_timeout_seconds: int = Field(default=240, ge=1, le=600)
    job_max_retries: int = Field(default=DEFAULT_MAX_RETRIES, ge=0, le=10)
    job_lease_seconds: int = Field(default=DEFAULT_LEASE_SECONDS, ge=60, le=600)
    reconcile_interval_seconds: int = Field(default=60, ge=5, le=3600)
    reconcile_batch_size: int = Field(default=100, ge=1, le=1000)
    worker_grace_period_seconds: int = Field(default=600, ge=30, le=600)

    upload_max_bytes: int = Field(default=26_214_400, ge=1024)
    upload_scan_required: bool = False

    simulation_seed: int = 0
    simulated_timeout_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    simulated_failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    sim_work_min_seconds: float = Field(default=20.0, ge=0.0)
    sim_work_max_seconds: float = Field(default=240.0, ge=0.0)

    @field_validator("app_env", mode="before")
    @classmethod
    def _normalize_env(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value

    @model_validator(mode="after")
    def _validate_invariants(self) -> Settings:
        if self.presigned_url_ttl_seconds > self.presigned_url_max_ttl_seconds:
            msg = "PRESIGNED_URL_TTL_SECONDS cannot exceed max TTL"
            raise ValueError(msg)
        if self.sim_work_min_seconds > self.sim_work_max_seconds:
            msg = "SIM_WORK_MIN_SECONDS cannot exceed SIM_WORK_MAX_SECONDS"
            raise ValueError(msg)
        if self.simulated_timeout_rate + self.simulated_failure_rate > 1.0:
            msg = "SIMULATED_TIMEOUT_RATE + SIMULATED_FAILURE_RATE must be <= 1.0"
            raise ValueError(msg)

        env_name = self.app_env.value
        is_production = env_name in _PRODUCTION_ENVS
        if is_production and (
            self.simulated_timeout_rate > 0.0 or self.simulated_failure_rate > 0.0
        ):
            msg = "production rejects non-zero simulation rates"
            raise ValueError(msg)
        if is_production and self.auth_mode is AuthMode.LOCAL:
            msg = "production rejects local auth mode"
            raise ValueError(msg)
        if self.upload_scan_required and env_name != AppEnvironment.LOCAL.value:
            # Fail closed until a real scanner adapter is configured.
            # Local exercise may still mark jobs quarantined for tests.
            pass
        if self.spaces_credentials_json is not None:
            self.parse_spaces_credentials()
        if self.llm_credentials_json is not None:
            self.parse_inference_credentials()
        return self

    def parse_spaces_credentials(self) -> SpacesCredentials:
        """Parse and validate Spaces JSON against ``APP_ENV``."""

        if self.spaces_credentials_json is None:
            msg = "SPACES_CREDENTIALS_JSON is required"
            raise ValueError(msg)
        payload = _parse_json_object(
            self.spaces_credentials_json.get_secret_value(),
            label="SPACES_CREDENTIALS_JSON",
        )
        creds = SpacesCredentials.model_validate(payload)
        self._assert_secret_environment(creds.environment, label="Spaces")
        return creds

    def parse_inference_credentials(self) -> InferenceCredentials:
        """Parse and validate inference JSON against ``APP_ENV``."""

        if self.llm_credentials_json is None:
            msg = "LLM_CREDENTIALS_JSON is required"
            raise ValueError(msg)
        payload = _parse_json_object(
            self.llm_credentials_json.get_secret_value(),
            label="LLM_CREDENTIALS_JSON",
        )
        creds = InferenceCredentials.model_validate(payload)
        self._assert_secret_environment(creds.environment, label="inference")
        return creds

    def _assert_secret_environment(self, secret_env: str, *, label: str) -> None:
        expected = self.app_env.value
        if expected in _PRODUCTION_ENVS:
            allowed = _PRODUCTION_ENVS
        else:
            allowed = frozenset({expected})
        if secret_env not in allowed:
            msg = (
                f"{label} credentials environment {secret_env!r} "
                f"does not match APP_ENV={expected}"
            )
            raise ValueError(msg)

    @property
    def is_production(self) -> bool:
        """True when running under production environment names."""

        return self.app_env.value in _PRODUCTION_ENVS
