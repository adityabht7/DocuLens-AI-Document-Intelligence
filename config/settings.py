"""DocuLens Configuration Settings
Centralized settings for application constants, model parameters, and storage paths.
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
SAMPLE_DOCS_DIR = BASE_DIR / "sample_docs"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure runtime directories exist
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Document Processing Settings
MAX_FILE_SIZE_MB = 25
ALLOWED_EXTENSIONS = [".pdf"]
DEFAULT_CHUNK_SIZE = 500  # characters (~100-125 tokens)
DEFAULT_CHUNK_OVERLAP = 80  # characters overlap
MIN_TEXT_PER_PAGE = 20  # Below this threshold, flag as scanned/image-only

# Embedding Model Settings
# sentence-transformers/all-MiniLM-L6-v2 outputs 384-dimensional dense vectors
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Vector DB Settings
CHROMA_COLLECTION_NAME = "doculens_documents"

# Retrieval Settings
DEFAULT_TOP_K = 5
SIMILARITY_THRESHOLD = 0.25  # Minimum relevance threshold for candidate retrieval

# LLM / Ollama Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
FALLBACK_OLLAMA_MODEL = "llama3.2:1b"
LLM_TIMEOUT_SECONDS = 45

# Category Definitions
DOCUMENT_CATEGORIES = [
    "Academic & Research",
    "Company & Financial",
    "Policy & Compliance",
    "Technical Documentation",
    "General Document"
]
