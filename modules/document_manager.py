"""Document Manager Module
Fulfills:
- FR-01: PDF upload coordination
- FR-02: Multiple uploads
- FR-03: File validation & duplicate detection (SHA-256)
- FR-06: Document listing & metadata registry
- FR-07: Document deletion (ChromaDB + registry)
"""
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from config.settings import DATA_DIR, SAMPLE_DOCS_DIR
from modules.embeddings import generate_embeddings
from modules.pdf_extractor import PDFValidationError, extract_text_from_pdf
from modules.summarizer import detect_document_category
from modules.text_chunker import chunk_document_pages
from modules.vector_store import (
    add_chunks_to_vector_store,
    delete_document_from_vector_store,
    get_vector_store_stats,
)

METADATA_REGISTRY_FILE = DATA_DIR / "document_registry.json"


def load_registry() -> Dict[str, Dict[str, Any]]:
    """Loads persistent document metadata registry."""
    if METADATA_REGISTRY_FILE.exists():
        try:
            with open(METADATA_REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_registry(registry: Dict[str, Dict[str, Any]]) -> None:
    """Saves document metadata registry to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(METADATA_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def is_duplicate_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    """Checks whether a document with the identical SHA-256 hash has already been indexed."""
    registry = load_registry()
    for doc in registry.values():
        if doc.get("file_hash") == file_hash:
            return doc
    return None


def process_and_index_pdf(
    file_source: Union[bytes, str, Path],
    file_name: str
) -> Tuple[bool, str, Dict[str, Any]]:
    """Complete document ingestion pipeline.
    
    1. Validates PDF format, size, and magic signature.
    2. Checks for duplicates via SHA-256.
    3. Extracts text page-by-page.
    4. Chunks text while retaining page numbers.
    5. Generates embeddings using Sentence Transformers.
    6. Stores chunks & embeddings in ChromaDB.
    7. Updates document registry with category and page counts.
    
    Returns:
        (success: bool, message: str, doc_info: dict)
    """
    try:
        pages, doc_meta = extract_text_from_pdf(file_source, file_name)
    except PDFValidationError as e:
        return False, str(e), {}
    except Exception as e:
        return False, f"Unexpected extraction error for '{file_name}': {str(e)}", {}

    file_hash = doc_meta["file_hash"]

    # Check for duplicate file
    existing = is_duplicate_hash(file_hash)
    if existing:
        return False, f"Document '{file_name}' is a duplicate of '{existing['file_name']}' (identical SHA-256 fingerprint).", existing

    # Check if document has no readable text (e.g. scanned)
    if doc_meta["is_entirely_scanned"] or doc_meta["total_chars"] == 0:
        return False, f"Document '{file_name}' appears to be a scanned image or empty PDF. OCR is not supported in the MVP release.", doc_meta

    document_id = str(uuid.uuid4())[:8]

    # Chunk document pages
    chunks = chunk_document_pages(pages, document_id=document_id)
    if not chunks:
        return False, f"No processable text passages could be chunked for '{file_name}'.", doc_meta

    # Generate embeddings
    chunk_texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(chunk_texts, normalize=True)

    # Store in ChromaDB
    added_count = add_chunks_to_vector_store(chunks, embeddings)

    # Detect category from aggregated text
    sample_text = " ".join([p["clean_text"] for p in pages[:3]])
    cat_result = detect_document_category(sample_text, file_name)

    # Save to registry
    registry = load_registry()
    doc_record = {
        "document_id": document_id,
        "file_name": file_name,
        "file_hash": file_hash,
        "page_count": doc_meta["page_count"],
        "total_chars": doc_meta["total_chars"],
        "chunk_count": len(chunks),
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": cat_result["category"],
        "category_confidence": cat_result["confidence"],
        "has_scanned_pages": doc_meta["has_scanned_pages"],
        "processing_status": "completed"
    }
    registry[document_id] = doc_record
    save_registry(registry)

    # Save physical copy in sample_docs if bytes were passed
    try:
        if isinstance(file_source, bytes):
            dest_path = SAMPLE_DOCS_DIR / file_name
            with open(dest_path, "wb") as f:
                f.write(file_source)
    except Exception:
        pass

    msg = f"Successfully indexed '{file_name}' ({doc_meta['page_count']} pages, {len(chunks)} chunks)."
    return True, msg, doc_record


def delete_document(document_id: str) -> Tuple[bool, str]:
    """Completely removes a document from ChromaDB and registry.
    
    Fulfills FR-07 & Security Requirement 4.
    """
    registry = load_registry()
    if document_id not in registry:
        return False, f"Document ID '{document_id}' not found in registry."

    doc_info = registry[document_id]
    file_name = doc_info["file_name"]

    # Delete from ChromaDB
    deleted_chunks = delete_document_from_vector_store(document_id=document_id)

    # Delete from registry
    del registry[document_id]
    save_registry(registry)

    # Optionally remove local file if present
    file_path = SAMPLE_DOCS_DIR / file_name
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    return True, f"Document '{file_name}' and its {deleted_chunks} vector chunks were permanently removed."


def list_indexed_documents() -> List[Dict[str, Any]]:
    """Returns a list of all currently indexed documents in the platform."""
    registry = load_registry()
    return list(registry.values())
