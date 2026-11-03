"""Retriever Module for Semantic and Hybrid Search
Fulfills:
- FR-12: Semantic search (Retrieve passages based on meaning)
- FR-13: Relevance ranking (Rank retrieved passages by relevance score)
- FR-22: Multi-document search (Search across multiple or all documents)
- FR-24: Relevant excerpt display (Extract supporting evidence)
"""
import re
from typing import Any, Dict, List, Optional
from config.settings import DEFAULT_TOP_K, SIMILARITY_THRESHOLD
from modules.embeddings import generate_query_embedding
from modules.vector_store import get_or_create_collection


def calculate_keyword_score(query: str, text: str) -> float:
    """Calculates a simple lexical/term overlap score between query and passage."""
    query_words = set(re.findall(r'\w+', query.lower()))
    text_words = set(re.findall(r'\w+', text.lower()))
    if not query_words or not text_words:
        return 0.0
    common = query_words.intersection(text_words)
    return len(common) / len(query_words)


def retrieve_relevant_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    document_filter: Optional[str] = None,
    hybrid_alpha: float = 0.85
) -> List[Dict[str, Any]]:
    """Retrieves top relevant chunks from ChromaDB for a given natural language query.
    
    Args:
        query: User question or search phrase.
        top_k: Number of relevant passages to retrieve.
        document_filter: Optional file_name or document_id to limit search scope.
        hybrid_alpha: Weight given to semantic score (0.85 semantic, 0.15 keyword overlap).
        
    Returns:
        List of ranked passages with metadata and similarity scores:
            - chunk_id: Unique chunk ID
            - text: Text excerpt
            - file_name: Source document name
            - page_number: 1-indexed source page
            - chunk_index: Position in document
            - similarity_score: Normalized similarity score (0.0 to 1.0)
            - hybrid_score: Combined semantic + lexical score
    """
    if not query.strip():
        return []

    collection = get_or_create_collection()
    if collection.count() == 0:
        return []

    query_vector = generate_query_embedding(query, normalize=True)

    where_filter = None
    if document_filter:
        where_filter = {"file_name": document_filter}

    # Fetch extra candidates for hybrid reranking
    fetch_k = min(collection.count(), max(top_k * 3, 10))

    query_params = {
        "query_embeddings": [query_vector],
        "n_results": fetch_k,
        "include": ["documents", "metadatas", "distances"]
    }
    if where_filter:
        query_params["where"] = where_filter

    results = collection.query(**query_params)

    if not results or not results["documents"] or not results["documents"][0]:
        return []

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
    ids = results["ids"][0] if results.get("ids") else [f"chunk_{i}" for i in range(len(docs))]

    candidates: List[Dict[str, Any]] = []

    for i in range(len(docs)):
        text = docs[i]
        meta = metadatas[i]
        distance = distances[i]

        # Cosine distance to similarity: cosine_sim = 1 - distance
        semantic_sim = max(0.0, min(1.0, 1.0 - float(distance)))
        keyword_score = calculate_keyword_score(query, text)

        # Hybrid score combines dense vector similarity with sparse lexical matching
        hybrid_score = (hybrid_alpha * semantic_sim) + ((1.0 - hybrid_alpha) * keyword_score)

        candidates.append({
            "chunk_id": ids[i],
            "text": text,
            "document_id": meta.get("document_id", ""),
            "file_name": meta.get("file_name", "Unknown"),
            "page_number": int(meta.get("page_number", 1)),
            "chunk_index": int(meta.get("chunk_index", 0)),
            "similarity_score": round(semantic_sim, 4),
            "keyword_score": round(keyword_score, 4),
            "hybrid_score": round(hybrid_score, 4)
        })

    # Sort candidates by hybrid score descending
    candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)

    # Filter out entries below threshold if we have enough results
    filtered = [c for c in candidates if c["similarity_score"] >= SIMILARITY_THRESHOLD]
    if not filtered:
        filtered = candidates[:top_k]
    else:
        filtered = filtered[:top_k]

    return filtered
