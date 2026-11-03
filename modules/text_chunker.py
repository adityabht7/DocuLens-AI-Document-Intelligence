"""Text Chunking Module
Fulfills FR-09: Divide documents into smaller passages, preserving metadata and page tracking.
"""
import re
from typing import Dict, List, Optional
from config.settings import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE


def split_into_sentences(text: str) -> List[str]:
    """Splits text into sentences based on punctuation and whitespace."""
    if not text:
        return []
    # Match sentence endings: period, question mark, exclamation mark followed by space or newline
    sentence_end_pattern = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_end_pattern.split(text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[str]:
    """Splits a single text string into overlapping chunks respecting sentence boundaries.
    
    Args:
        text: The input text to chunk.
        chunk_size: Maximum target character size per chunk.
        chunk_overlap: Number of characters to overlap between successive chunks.
        
    Returns:
        List of chunk strings.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    sentences = split_into_sentences(text)
    if not sentences:
        # Fallback to character slicing if no clear sentence boundaries
        chunks = []
        step = max(1, chunk_size - chunk_overlap)
        for i in range(0, len(text), step):
            chunk = text[i:i + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        
        # If a single sentence exceeds chunk_size, split it on word boundaries
        if sentence_len > chunk_size:
            words = sentence.split(' ')
            sub_chunk = []
            sub_len = 0
            for word in words:
                word_len = len(word) + 1
                if sub_len + word_len > chunk_size and sub_chunk:
                    chunks.append(" ".join(sub_chunk).strip())
                    # Retain last few words for overlap
                    overlap_words = []
                    acc = 0
                    for w in reversed(sub_chunk):
                        if acc + len(w) + 1 <= chunk_overlap:
                            overlap_words.insert(0, w)
                            acc += len(w) + 1
                        else:
                            break
                    sub_chunk = overlap_words + [word]
                    sub_len = sum(len(w) + 1 for w in sub_chunk)
                else:
                    sub_chunk.append(word)
                    sub_len += word_len
            if sub_chunk:
                chunks.append(" ".join(sub_chunk).strip())
            continue

        if current_length + sentence_len + 1 > chunk_size and current_chunk:
            chunk_str = " ".join(current_chunk).strip()
            chunks.append(chunk_str)

            # Build overlap from the end of current_chunk
            overlap_sentences = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) + 1 <= chunk_overlap:
                    overlap_sentences.insert(0, s)
                    overlap_length += len(s) + 1
                else:
                    break

            current_chunk = overlap_sentences + [sentence]
            current_length = sum(len(s) + 1 for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_length += sentence_len + 1

    if current_chunk:
        chunk_str = " ".join(current_chunk).strip()
        if not chunks or chunk_str != chunks[-1]:
            chunks.append(chunk_str)

    return chunks


def chunk_document_pages(
    pages: List[Dict[str, any]],
    document_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[Dict[str, any]]:
    """Chunks extracted document pages while rigorously preserving page numbers and document metadata.
    
    Args:
        pages: Output list from extract_text_from_pdf containing page metadata.
        document_id: Unique identifier for the document.
        chunk_size: Maximum target characters per chunk.
        chunk_overlap: Overlap characters between chunks.
        
    Returns:
        List of chunk dicts ready for ChromaDB and embedding generation:
            - chunk_id: f"{document_id}_p{page_number}_c{chunk_index}"
            - document_id: ID of the parent document
            - file_name: Source PDF name
            - page_number: 1-indexed page number
            - chunk_index: Relative chunk position within the document
            - text: Text content of the chunk
            - char_count: Length of the chunk text
    """
    all_chunks: List[Dict[str, any]] = []
    chunk_counter = 0

    for page in pages:
        clean_text = page.get("clean_text", "").strip()
        if not clean_text:
            continue

        page_num = page["page_number"]
        doc_name = page["document_name"]

        page_chunks = chunk_text(
            clean_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        for page_chunk_idx, text_segment in enumerate(page_chunks):
            chunk_counter += 1
            chunk_id = f"{document_id}_p{page_num}_c{page_chunk_idx}"

            all_chunks.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "file_name": doc_name,
                "page_number": page_num,
                "chunk_index": chunk_counter,
                "text": text_segment,
                "char_count": len(text_segment)
            })

    return all_chunks
