"""Script to pre-index sample documents into DocuLens vector store.
"""
from pathlib import Path
from modules.document_manager import list_indexed_documents, process_and_index_pdf
from config.settings import SAMPLE_DOCS_DIR


def index_sample_documents():
    pdf_files = list(SAMPLE_DOCS_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} sample PDFs to index.")

    for pdf in pdf_files:
        with open(pdf, "rb") as f:
            pdf_bytes = f.read()
        success, message, doc_record = process_and_index_pdf(pdf_bytes, pdf.name)
        print(f"[{'SUCCESS' if success else 'SKIPPED'}] {pdf.name}: {message}")

    indexed = list_indexed_documents()
    print(f"\nTotal currently indexed documents: {len(indexed)}")


if __name__ == "__main__":
    index_sample_documents()
