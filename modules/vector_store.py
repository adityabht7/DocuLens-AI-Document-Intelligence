"""Vector Store Module using ChromaDB
Fulfills:
- FR-11: Vector storage (Store embeddings, text passages, and document metadata)
- FR-07: Document deletion (Remove documents and associated embeddings completely)
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings

from config.settings import CHROMA_COLLECTION_NAME, CHROMA_DIR

# Singleton client instance
_CHROMA_CLIENT = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns the persistent ChromaDB client singleton."""
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
    return _CHROMA_CLIENT


def get_or_create_collection(collection_name: str = CHROMA_COLLECTION_NAME):
    """Retrieves or creates the target ChromaDB collection with cosine distance metric."""
    client = get_chroma_client()
    # Using cosine distance metric for normalized sentence embeddings
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def add_chunks_to_vector_store(
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    collection_name: str = CHROMA_COLLECTION_NAME
) -> int:
    """Inserts document chunks, vectors, and metadata into ChromaDB.
    
    Args:
        chunks: List of chunk dictionaries containing text and metadata.
        embeddings: List of embedding vectors matching chunks.
        collection_name: Target Chroma collection name.
        
    Returns:
        Number of successfully inserted chunks.
    """
    if not chunks or not embeddings:
        return 0

    if len(chunks) != len(embeddings):
        raise ValueError(f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings.")

    collection = get_or_create_collection(collection_name)

    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "document_id": str(c["document_id"]),
            "file_name": str(c["file_name"]),
            "page_number": int(c["page_number"]),
            "chunk_index": int(c["chunk_index"]),
            "char_count": int(c.get("char_count", len(c["text"])))
        }
        for c in chunks
    ]

    # ChromaDB supports upsert so re-indexing does not cause ID collision
    batch_size = 200
    total_added = 0
    for i in range(0, len(ids), batch_size):
        end_idx = min(i + batch_size, len(ids))
        collection.upsert(
            ids=ids[i:end_idx],
            embeddings=embeddings[i:end_idx],
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx]
        )
        total_added += (end_idx - i)

    return total_added


def delete_document_from_vector_store(
    document_id: Optional[str] = None,
    file_name: Optional[str] = None,
    collection_name: str = CHROMA_COLLECTION_NAME
) -> int:
    """Deletes all chunks and embeddings for a given document.
    
    Args:
        document_id: Unique ID of the document to remove.
        file_name: Name of the file to remove.
        collection_name: Target Chroma collection.
        
    Returns:
        Number of items deleted (or 1 if matched).
    """
    collection = get_or_create_collection(collection_name)

    where_filter = {}
    if document_id:
        where_filter["document_id"] = str(document_id)
    elif file_name:
        where_filter["file_name"] = str(file_name)
    else:
        return 0

    # Retrieve matching chunk IDs to verify deletion count
    existing = collection.get(where=where_filter, include=["metadatas"])
    count = len(existing["ids"]) if existing and "ids" in existing else 0

    if count > 0:
        collection.delete(where=where_filter)

    return count


def get_vector_store_stats(collection_name: str = CHROMA_COLLECTION_NAME) -> Dict[str, Any]:
    """Retrieves high-level statistics about the stored vectors and documents."""
    collection = get_or_create_collection(collection_name)
    total_chunks = collection.count()

    documents_set = set()
    pages_per_doc: Dict[str, set] = {}

    if total_chunks > 0:
        data = collection.get(include=["metadatas"])
        if data and "metadatas" in data and data["metadatas"]:
            for meta in data["metadatas"]:
                doc_name = meta.get("file_name", "Unknown")
                page_num = meta.get("page_number", 1)
                documents_set.add(doc_name)
                if doc_name not in pages_per_doc:
                    pages_per_doc[doc_name] = set()
                pages_per_doc[doc_name].add(page_num)

    return {
        "total_chunks": total_chunks,
        "total_documents": len(documents_set),
        "document_names": sorted(list(documents_set)),
        "document_pages_count": {doc: len(pages) for doc, pages in pages_per_doc.items()}
    }


def reset_vector_store(collection_name: str = CHROMA_COLLECTION_NAME) -> None:
    """Deletes and recreates the ChromaDB collection."""
    client = get_chroma_client()
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    get_or_create_collection(collection_name)
