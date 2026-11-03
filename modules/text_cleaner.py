"""Text Cleaning and Normalization Module
Fulfills FR-08: Text cleaning (removes unwanted formatting and extra whitespace).
"""
import re
import unicodedata


def clean_text(text: str) -> str:
    """Cleans raw text extracted from PDF pages.
    
    1. Normalizes unicode characters (ligatures, accents, quotes).
    2. Replaces soft-hyphen line wraps (e.g., 'approv-\\nal' -> 'approval').
    3. Normalizes whitespace and line breaks while preserving paragraph boundaries.
    4. Strips control characters and non-printable noise.
    
    Args:
        text: Raw text string from PDF extractor.
        
    Returns:
        Cleaned, normalized text string.
    """
    if not text:
        return ""

    # Normalize unicode to standard NFKC
    text = unicodedata.normalize("NFKC", text)

    # Standardize curly quotes and fancy dashes
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("\u2022", " - ")  # bullet points to dash

    # Resolve hyphenated word breaks at newlines: 'docu-\nment' -> 'document'
    text = re.sub(r'(\b\w+)-\s*\n\s*(\w+\b)', r'\1\2', text)

    # Replace multiple newline sequences (3+) with double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Replace multiple spaces/tabs within a line with a single space
    text = re.sub(r'[ \t]+', ' ', text)

    # Strip non-printable / control characters except standard newlines and tabs
    text = "".join(ch for ch in text if ch == '\n' or ch == '\t' or unicodedata.category(ch)[0] != 'C')

    # Remove trailing/leading spaces on each line
    lines = [line.strip() for line in text.split('\n')]
    cleaned = '\n'.join(lines)

    # Trim leading/trailing whitespace
    return cleaned.strip()
