"""Unit tests for PDF Extractor module
Fulfills Section 14.1 Unit Testing for PDF Extractor.
"""
import io
import pytest
from pypdf import PdfWriter

from modules.pdf_extractor import (
    PDFValidationError,
    compute_sha256,
    extract_text_from_pdf,
    validate_pdf_bytes,
)


def create_minimal_pdf_bytes(text: str = "Hello DocuLens Test Page") -> bytes:
    """Helper to create a valid minimal PDF in-memory."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # Write to bytes stream
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_validate_pdf_valid_header():
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    # Should not raise exception
    validate_pdf_bytes(pdf_bytes, "test.pdf")


def test_validate_pdf_invalid_signature():
    with pytest.raises(PDFValidationError, match="not a valid PDF file"):
        validate_pdf_bytes(b"NOT_A_PDF_CONTENT", "fake.pdf")


def test_validate_pdf_empty_bytes():
    with pytest.raises(PDFValidationError, match="empty"):
        validate_pdf_bytes(b"", "empty.pdf")


def test_compute_sha256():
    data = b"DocuLens Test 123"
    h1 = compute_sha256(data)
    h2 = compute_sha256(data)
    assert h1 == h2
    assert len(h1) == 64


def test_extract_text_from_sample_pdf():
    from config.settings import SAMPLE_DOCS_DIR
    sample_path = SAMPLE_DOCS_DIR / "Edge_Case_Test_Doc.pdf"
    if not sample_path.exists():
        pytest.skip("Sample PDF not found.")

    pages, meta = extract_text_from_pdf(sample_path, "Edge_Case_Test_Doc.pdf")
    assert meta["page_count"] == 1
    assert "ALPHA-OMEGA-9942" in pages[0]["clean_text"]
    assert pages[0]["page_number"] == 1
    assert not pages[0]["is_scanned"]


def test_handle_corrupted_pdf():
    corrupted_bytes = b"%PDF-corrupted-data-header-without-valid-trailer"
    with pytest.raises(PDFValidationError):
        extract_text_from_pdf(corrupted_bytes, "corrupted.pdf")
