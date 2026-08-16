# SPDX-License-Identifier: MIT
"""Bounded PDF validation helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

PDF_MAGIC = b"%PDF-"


class UploadValidationError(ValueError):
    """Raised when an upload fails synchronous validation."""


@dataclass(frozen=True, slots=True)
class ValidatedPdf:
    """Validated PDF bytes and hash."""

    content: bytes
    sha256: str
    size_bytes: int


def validate_pdf_bytes(
    data: bytes,
    *,
    max_bytes: int,
    content_type: str | None = None,
) -> ValidatedPdf:
    """Validate size, optional content-type, and PDF magic bytes."""

    if max_bytes <= 0:
        msg = "max_bytes must be positive"
        raise UploadValidationError(msg)
    if len(data) == 0:
        raise UploadValidationError("empty upload")
    if len(data) > max_bytes:
        raise UploadValidationError("upload exceeds size limit")
    if content_type is not None and content_type.lower() not in {
        "application/pdf",
        "application/x-pdf",
    }:
        raise UploadValidationError("unsupported content type")
    if not data.startswith(PDF_MAGIC):
        raise UploadValidationError("file is not a PDF")
    # Reject encrypted PDFs by common marker without claiming full crypto analysis.
    if b"/Encrypt" in data[: min(len(data), 1_048_576)]:
        raise UploadValidationError("encrypted PDFs are not supported")
    digest = hashlib.sha256(data).hexdigest()
    return ValidatedPdf(content=data, sha256=digest, size_bytes=len(data))


def sanitize_filename(name: str | None) -> str | None:
    """Retain a short sanitized filename as metadata only."""

    if name is None:
        return None
    cleaned = name.replace("\\", "/").split("/")[-1].strip()
    if not cleaned:
        return None
    return cleaned[:255]
