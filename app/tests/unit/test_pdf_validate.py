# SPDX-License-Identifier: MIT
"""Unit tests for PDF validation."""

from __future__ import annotations

import pytest

from halcyon_sim.pdf_validate import (
    UploadValidationError,
    sanitize_filename,
    validate_pdf_bytes,
)


def test_validate_pdf_accepts_magic_bytes() -> None:
    payload = b"%PDF-1.4\n%EOF"
    result = validate_pdf_bytes(payload, max_bytes=1024, content_type="application/pdf")
    assert result.size_bytes == len(payload)
    assert len(result.sha256) == 64


def test_validate_pdf_rejects_oversized_and_non_pdf() -> None:
    with pytest.raises(UploadValidationError, match="size"):
        validate_pdf_bytes(b"%PDF-" + b"x" * 20, max_bytes=10)
    with pytest.raises(UploadValidationError, match="not a PDF"):
        validate_pdf_bytes(b"not-a-pdf", max_bytes=1024)


def test_validate_pdf_rejects_encrypt_marker() -> None:
    with pytest.raises(UploadValidationError, match="encrypted"):
        validate_pdf_bytes(b"%PDF-1.4\n/Encrypt\n", max_bytes=1024)


def test_sanitize_filename_strips_path() -> None:
    assert sanitize_filename("../secret/contract.pdf") == "contract.pdf"
    assert sanitize_filename("") is None
