"""Unit tests for RAG Pipeline module
Fulfills Section 14.1 Unit Testing for RAG Pipeline.
"""
from modules.rag_pipeline import (
    answer_question,
    format_context_prompt,
    generate_local_extractive_answer,
)


def test_format_context_prompt():
    chunks = [
        {
            "file_name": "Report_2025.pdf",
            "page_number": 2,
            "text": "Revenue surged by 22.4% year-over-year."
        }
    ]
    prompt_str = format_context_prompt(chunks)
    assert "Report_2025.pdf" in prompt_str
    assert "Page Number: 2" in prompt_str
    assert "Revenue surged" in prompt_str


def test_empty_context_refusal():
    result = answer_question("What is the secret formula?", top_k=5)
    # When no matching chunks are present, it should gracefully refuse to hallucinate
    assert "insufficient evidence" in result["answer"].lower() or "cannot be answered" in result["answer"].lower() or not result["grounded"]


def test_local_extractive_answer_with_evidence():
    chunks = [
        {
            "file_name": "Company_Policy.pdf",
            "page_number": 1,
            "similarity_score": 0.85,
            "text": "All full-time employees are entitled to 24 business days of paid annual leave per calendar year."
        }
    ]
    ans = generate_local_extractive_answer("How many days of paid leave are allowed?", chunks)
    assert "24 business days" in ans
    assert "Doc: Company_Policy.pdf" in ans
    assert "Page: 1" in ans
