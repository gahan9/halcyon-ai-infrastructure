# SPDX-License-Identifier: MIT
"""Authentication adapter: principal → immutable vendor_id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import HTTPException, status

from halcyon_sim.config import AppEnvironment, AuthMode, Settings


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated caller identity."""

    subject: str
    vendor_id: UUID


class AuthProvider(Protocol):
    """Convert a bearer token or local header into a Principal."""

    async def authenticate(self, authorization: str | None) -> Principal:
        """Return a principal or raise HTTP 401/403."""


class FakeAuthProvider:
    """Deterministic local/test issuer. Forbidden outside APP_ENV=local."""

    def __init__(self, *, app_env: AppEnvironment) -> None:
        if app_env is not AppEnvironment.LOCAL:
            msg = "FakeAuthProvider is only permitted when APP_ENV=local"
            raise RuntimeError(msg)
        self._app_env = app_env

    async def authenticate(self, authorization: str | None) -> Principal:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing bearer token",
            )
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="empty bearer token",
            )
        vendor_id = uuid5(NAMESPACE_URL, f"halcyon-local-vendor:{token}")
        return Principal(subject=token, vendor_id=vendor_id)


class FailClosedAuthProvider:
    """Placeholder until Dana selects a real identity provider."""

    async def authenticate(self, authorization: str | None) -> Principal:
        del authorization
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="identity provider is not configured",
        )


def build_auth_provider(settings: Settings) -> AuthProvider:
    """Select the auth adapter from settings."""

    if settings.auth_mode is AuthMode.LOCAL:
        return FakeAuthProvider(app_env=settings.app_env)
    return FailClosedAuthProvider()
