"""PDF Extraction and Validation Module
Fulfills:
- FR-01: PDF upload
- FR-02: Multiple uploads
- FR-03: File validation (file type, size, signature, readability)
- FR-04: Text extraction per page
- FR-05: Page tracking (document name, page number, metadata)
"""
import hashlib
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from config.settings import MAX_FILE_SIZE_MB, MIN_TEXT_PER_PAGE
from modules.text_cleaner import clean_text


class PDFValidationError(Exception):
    """Raised when PDF validation fails (invalid file, too large, unreadable)."""
    pass


def compute_sha256(file_bytes: bytes) -> str:
    """Computes SHA-256 fingerprint of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def validate_pdf_bytes(file_bytes: bytes, file_name: str) -> None:
    """Validates the PDF file bytes for size and correct PDF header signature.
    
    Args:
        file_bytes: Raw bytes of the uploaded file.
        file_name: Name of the file.
        
    Raises:
        PDFValidationError: If file violates size or signature rules.
    """
    if not file_bytes:
        raise PDFValidationError(f"File '{file_name}' is empty (0 bytes).")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise PDFValidationError(
            f"File '{file_name}' exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB (size: {size_mb:.2f}MB)."
        )

    # Security check: Check magic number / signature (must begin with %PDF-)
    # Streamlit file extension is not sufficient protection
    if not file_bytes.startswith(b"%PDF-"):
        raise PDFValidationError(
            f"File '{file_name}' is not a valid PDF file (invalid magic signature)."
        )


def extract_text_from_pdf(
    file_source: Union[bytes, io.BytesIO, str, Path],
    file_name: str
) -> Tuple[List[Dict[str, Union[str, int, bool]]], Dict[str, Union[str, int, bool]]]:
    """Extracts text page-by-page from a PDF while tracking page numbers and metadata.
    
    Args:
        file_source: File bytes, stream, or file path.
        file_name: Name of the document.
        
    Returns:
        Tuple of:
            - pages: List of dicts, each with keys:
                'document_name', 'page_number', 'raw_text', 'clean_text', 'char_count', 'is_scanned'
            - document_metadata: Dict with document summary info:
                'file_name', 'file_hash', 'page_count', 'total_chars', 'has_scanned_pages'
                
    Raises:
        PDFValidationError: If PDF is corrupt, password-protected, or unreadable.
    """
    if isinstance(file_source, (str, Path)):
        with open(file_source, "rb") as f:
            file_bytes = f.read()
    elif isinstance(file_source, io.BytesIO):
        file_bytes = file_source.getvalue()
    elif isinstance(file_source, bytes):
        file_bytes = file_source
    else:
        raise PDFValidationError(f"Unsupported file source type: {type(file_source)}")

    # Validate signature and size
    validate_pdf_bytes(file_bytes, file_name)

    file_hash = compute_sha256(file_bytes)

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except (PdfReadError, Exception) as e:
        raise PDFValidationError(f"Could not read PDF structure for '{file_name}': {str(e)}")

    if reader.is_encrypted:
        try:
            # Attempt to decrypt with empty password (common for encrypted with no password)
            decrypt_result = reader.decrypt("")
            if decrypt_result == 0:
                raise PDFValidationError(f"PDF '{file_name}' is password-protected and cannot be parsed.")
        except Exception:
            raise PDFValidationError(f"PDF '{file_name}' is password-protected and cannot be parsed.")

    page_count = len(reader.pages)
    if page_count == 0:
        raise PDFValidationError(f"PDF '{file_name}' contains 0 pages.")

    pages: List[Dict[str, Union[str, int, bool]]] = []
    scanned_pages_count = 0
    total_chars = 0

    for idx, page in enumerate(reader.pages, start=1):
        try:
            raw_text = page.extract_text() or ""
        except Exception as e:
            raw_text = ""

        cleaned = clean_text(raw_text)
        char_count = len(cleaned)
        is_scanned = char_count < MIN_TEXT_PER_PAGE

        if is_scanned:
            scanned_pages_count += 1

        pages.append({
            "document_name": file_name,
            "page_number": idx,
            "raw_text": raw_text,
            "clean_text": cleaned,
            "char_count": char_count,
            "is_scanned": is_scanned
        })
        total_chars += char_count

    doc_metadata = {
        "file_name": file_name,
        "file_hash": file_hash,
        "page_count": page_count,
        "total_chars": total_chars,
        "scanned_pages_count": scanned_pages_count,
        "has_scanned_pages": scanned_pages_count > 0,
        "is_entirely_scanned": scanned_pages_count == page_count
    }

    return pages, doc_metadata
