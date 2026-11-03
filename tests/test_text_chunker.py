"""Unit tests for Text Chunker module
Fulfills Section 14.1 Unit Testing for Text Chunker.
"""
from modules.text_chunker import chunk_document_pages, chunk_text, split_into_sentences


def test_split_into_sentences():
    text = "First sentence. Second sentence! Third sentence? Done."
    sentences = split_into_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "First sentence."
    assert sentences[1] == "Second sentence!"


def test_chunk_text_basic():
    # Long text
    text = "This is a detailed sentence about document intelligence platforms. " * 30
    chunks = chunk_text(text, chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    assert all(len(c) > 0 for c in chunks)
    # Check that chunks do not excessively exceed chunk_size
    for c in chunks:
        assert len(c) <= 350


def test_chunk_document_pages_preserves_metadata():
    pages = [
        {
            "document_name": "Report.pdf",
            "page_number": 1,
            "clean_text": "Executive overview on page one. " * 20
        },
        {
            "document_name": "Report.pdf",
            "page_number": 2,
            "clean_text": "Financial data breakdown on page two. " * 20
        }
    ]
    chunks = chunk_document_pages(pages, document_id="doc123", chunk_size=250, chunk_overlap=40)
    assert len(chunks) >= 2

    # Check page 1 chunks
    p1_chunks = [c for c in chunks if c["page_number"] == 1]
    p2_chunks = [c for c in chunks if c["page_number"] == 2]

    assert len(p1_chunks) > 0
    assert len(p2_chunks) > 0
    assert all(c["document_id"] == "doc123" for c in chunks)
    assert all(c["file_name"] == "Report.pdf" for c in chunks)
    assert all("chunk_id" in c for c in chunks)
