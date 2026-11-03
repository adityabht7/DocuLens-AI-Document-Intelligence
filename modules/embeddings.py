"""Embedding Generation Module
Fulfills FR-10: Convert text passages into numerical vectors using Sentence Transformers.
"""
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import EMBEDDING_DIMENSION, EMBEDDING_MODEL_NAME

# Global in-memory cache for the embedding model instance
_EMBEDDING_MODEL_INSTANCE = None


def get_embedding_model() -> SentenceTransformer:
    """Retrieves or initializes the SentenceTransformer model singleton.
    
    Returns:
        SentenceTransformer model loaded with all-MiniLM-L6-v2.
    """
    global _EMBEDDING_MODEL_INSTANCE
    if _EMBEDDING_MODEL_INSTANCE is None:
        _EMBEDDING_MODEL_INSTANCE = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _EMBEDDING_MODEL_INSTANCE


def generate_embeddings(
    texts: Union[str, List[str]],
    normalize: bool = True
) -> List[List[float]]:
    """Generates numerical vector embeddings for a text or list of texts.
    
    Args:
        texts: A single text string or list of text strings.
        normalize: Whether to normalize vectors to unit length (L2 norm) for cosine similarity.
        
    Returns:
        List of 384-dimensional float embeddings.
    """
    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=normalize,
        convert_to_numpy=True
    )

    # Convert numpy array to list of floats
    if isinstance(embeddings, np.ndarray):
        return embeddings.tolist()
    return [list(e) for e in embeddings]


def generate_query_embedding(query: str, normalize: bool = True) -> List[float]:
    """Generates an embedding vector for a single search query.
    
    Args:
        query: Natural language query string.
        normalize: Whether to normalize vector to unit length.
        
    Returns:
        384-dimensional float vector.
    """
    vectors = generate_embeddings([query], normalize=normalize)
    return vectors[0] if vectors else [0.0] * EMBEDDING_DIMENSION
