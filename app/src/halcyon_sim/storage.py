# SPDX-License-Identifier: MIT
"""Private Spaces object storage boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlparse
from uuid import UUID

import boto3

from halcyon_sim.config import Settings, SpacesCredentials


@dataclass(frozen=True, slots=True)
class StoredObject:
    """Reference to a private uploaded object."""

    bucket: str
    key: str
    vendor_id: UUID
    job_id: UUID


class ObjectStorage(Protocol):
    """Async-safe private object operations."""

    async def put_pdf(
        self,
        *,
        vendor_id: UUID,
        job_id: UUID,
        content: bytes,
        content_sha256: str,
    ) -> StoredObject:
        """Store a private PDF under a generated key."""

    async def delete(self, key: str) -> None:
        """Delete an object by key."""

    async def get_bytes(self, key: str) -> bytes:
        """Download object bytes."""

    async def create_presigned_get(
        self,
        *,
        key: str,
        vendor_id: UUID,
        ttl_seconds: int,
    ) -> str:
        """Create a GET-only temporary URL after ownership metadata checks."""


def object_key_for(vendor_id: UUID, job_id: UUID) -> str:
    """Generate the opaque Spaces key for a vendor job."""

    return f"vendors/{vendor_id}/jobs/{job_id}/source.pdf"


class InMemoryObjectStorage:
    """Test double for Spaces."""

    def __init__(self, bucket: str = "test-bucket") -> None:
        self.bucket = bucket
        self.objects: dict[str, bytes] = {}
        self.metadata: dict[str, dict[str, str]] = {}

    async def put_pdf(
        self,
        *,
        vendor_id: UUID,
        job_id: UUID,
        content: bytes,
        content_sha256: str,
    ) -> StoredObject:
        key = object_key_for(vendor_id, job_id)
        self.objects[key] = content
        self.metadata[key] = {
            "vendor_id": str(vendor_id),
            "job_id": str(job_id),
            "content_sha256": content_sha256,
        }
        return StoredObject(
            bucket=self.bucket, key=key, vendor_id=vendor_id, job_id=job_id
        )

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)
        self.metadata.pop(key, None)

    async def get_bytes(self, key: str) -> bytes:
        try:
            return self.objects[key]
        except KeyError as exc:
            msg = f"object not found: {key}"
            raise FileNotFoundError(msg) from exc

    async def create_presigned_get(
        self,
        *,
        key: str,
        vendor_id: UUID,
        ttl_seconds: int,
    ) -> str:
        meta = self.metadata.get(key)
        if meta is None or meta.get("vendor_id") != str(vendor_id):
            msg = "object ownership check failed"
            raise PermissionError(msg)
        return f"memory://{self.bucket}/{key}?ttl={ttl_seconds}"


class SpacesObjectStorage:  # pragma: no cover - requires live Spaces credentials
    """DigitalOcean Spaces adapter via boto3 in a worker thread."""

    def __init__(
        self,
        *,
        endpoint: str,
        bucket: str,
        region: str,
        credentials: SpacesCredentials,
    ) -> None:
        self._endpoint = endpoint
        self._bucket = bucket
        self._region = region
        self._credentials = credentials
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                region_name=self._region,
                endpoint_url=self._endpoint,
                aws_access_key_id=self._credentials.access_key.get_secret_value(),
                aws_secret_access_key=self._credentials.secret_key.get_secret_value(),
            )
        return self._client

    async def put_pdf(
        self,
        *,
        vendor_id: UUID,
        job_id: UUID,
        content: bytes,
        content_sha256: str,
    ) -> StoredObject:
        import asyncio

        key = object_key_for(vendor_id, job_id)

        def _put() -> None:
            self._get_client().put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentType="application/pdf",
                ACL="private",
                Metadata={
                    "vendor_id": str(vendor_id),
                    "job_id": str(job_id),
                    "content_sha256": content_sha256,
                },
            )

        await asyncio.to_thread(_put)
        return StoredObject(
            bucket=self._bucket,
            key=key,
            vendor_id=vendor_id,
            job_id=job_id,
        )

    async def delete(self, key: str) -> None:
        import asyncio

        def _delete() -> None:
            self._get_client().delete_object(Bucket=self._bucket, Key=key)

        await asyncio.to_thread(_delete)

    async def get_bytes(self, key: str) -> bytes:
        import asyncio

        def _get() -> bytes:
            response = self._get_client().get_object(Bucket=self._bucket, Key=key)
            body = response["Body"].read()
            assert isinstance(body, (bytes, bytearray))
            return bytes(body)

        return await asyncio.to_thread(_get)

    async def create_presigned_get(
        self,
        *,
        key: str,
        vendor_id: UUID,
        ttl_seconds: int,
    ) -> str:
        import asyncio

        def _sign() -> str:
            head = self._get_client().head_object(Bucket=self._bucket, Key=key)
            meta = {k.lower(): v for k, v in head.get("Metadata", {}).items()}
            if meta.get("vendor_id") != str(vendor_id):
                msg = "object ownership check failed"
                raise PermissionError(msg)
            url = self._get_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=ttl_seconds,
                HttpMethod="GET",
            )
            assert isinstance(url, str)
            return url

        return await asyncio.to_thread(_sign)


def build_object_storage(settings: Settings) -> ObjectStorage:
    """Build Spaces storage from settings, or fail if incomplete."""

    if (
        settings.spaces_endpoint is None
        or settings.spaces_bucket is None
        or settings.spaces_region is None
        or settings.spaces_credentials_json is None
    ):
        msg = "Spaces settings are incomplete"
        raise ValueError(msg)
    # Validate endpoint looks like a URL without logging secrets.
    parsed = urlparse(settings.spaces_endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        msg = "SPACES_ENDPOINT must be an http(s) URL"
        raise ValueError(msg)
    return SpacesObjectStorage(
        endpoint=settings.spaces_endpoint,
        bucket=settings.spaces_bucket,
        region=settings.spaces_region,
        credentials=settings.parse_spaces_credentials(),
    )
