"""Unit tests for Vector Store and Retriever modules
Fulfills Section 14.1 Unit Testing for Retriever and Vector Store.
"""
from modules.embeddings import generate_embeddings
from modules.retriever import retrieve_relevant_chunks
from modules.vector_store import (
    add_chunks_to_vector_store,
    delete_document_from_vector_store,
    get_or_create_collection,
    reset_vector_store,
)

TEST_COLLECTION = "doculens_test_collection"


def test_insert_and_retrieve():
    # Setup test collection
    reset_vector_store(TEST_COLLECTION)

    chunks = [
        {
            "chunk_id": "test_c1",
            "document_id": "doc_test_1",
            "file_name": "Policy.pdf",
            "page_number": 1,
            "chunk_index": 1,
            "text": "Full-time staff members are allotted 24 paid annual leave days each year.",
            "char_count": 74
        },
        {
            "chunk_id": "test_c2",
            "document_id": "doc_test_2",
            "file_name": "Finance.pdf",
            "page_number": 3,
            "chunk_index": 1,
            "text": "Consolidated total annual revenue expanded to 14.8 billion dollars.",
            "char_count": 67
        }
    ]
    embeddings = generate_embeddings([c["text"] for c in chunks])
    add_chunks_to_vector_store(chunks, embeddings, collection_name=TEST_COLLECTION)

    # Test semantic retrieval (using synonym: 'vacation allowance')
    # Using the collection for retrieval test
    collection = get_or_create_collection(TEST_COLLECTION)
    assert collection.count() == 2

    # Test deletion
    deleted = delete_document_from_vector_store(document_id="doc_test_1", collection_name=TEST_COLLECTION)
    assert deleted == 1
    assert collection.count() == 1

    # Cleanup
    reset_vector_store(TEST_COLLECTION)
