"""Unit tests for Embeddings module
Fulfills Section 14.1 Unit Testing for Embeddings.
"""
import math
from modules.embeddings import (
    generate_embeddings,
    generate_query_embedding,
    get_embedding_model,
)
from config.settings import EMBEDDING_DIMENSION


def test_embedding_model_singleton():
    m1 = get_embedding_model()
    m2 = get_embedding_model()
    assert m1 is m2


def test_generate_embeddings_dimension_and_norm():
    texts = [
        "What are the quarterly financial results?",
        "Employees can request time away from their duties for personal reasons."
    ]
    vectors = generate_embeddings(texts, normalize=True)
    assert len(vectors) == 2
    for vec in vectors:
        assert len(vec) == EMBEDDING_DIMENSION
        # Check unit normalization: sum of squares should be ~ 1.0
        norm_sq = sum(x * x for x in vec)
        assert math.isclose(norm_sq, 1.0, abs_tol=1e-3)


def test_generate_query_embedding():
    query = "How to apply for sick leave?"
    vec = generate_query_embedding(query, normalize=True)
    assert len(vec) == EMBEDDING_DIMENSION
    assert isinstance(vec[0], float)
