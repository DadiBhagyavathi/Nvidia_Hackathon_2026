"""
ingest_docs.py
──────────────
Location : backend/rag/ingest_docs.py
Run      : python backend/rag/ingest_docs.py
Purpose  : Read all PDFs from backend/rag/docs/, split into chunks,
           and index into ChromaDB via rag_pipeline.py.

How to add documents:
  1. Place any RBI / AML / PMLA PDF files into backend/rag/docs/
  2. Run this script once (or re-run to update the index)
  3. Existing chunks are NOT duplicated (checked by source+chunk_index)
"""

import sys
from pathlib import Path

# Make backend importable when run from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from loguru import logger
from pypdf import PdfReader
from backend.rag.rag_pipeline import ingest_texts, get_collection

DOCS_DIR   = Path(__file__).resolve().parent / "docs"
CHUNK_SIZE = 500   # characters
CHUNK_OVERLAP = 100


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Simple sliding-window chunker."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if len(c) > 50]  # drop tiny chunks


def pdf_to_chunks(pdf_path: Path) -> tuple[list[str], list[dict]]:
    """Extract text from PDF, chunk it, return (texts, metadatas)."""
    reader = PdfReader(str(pdf_path))
    full_text = "\n".join(
        page.extract_text() or "" for page in reader.pages
    )
    chunks    = chunk_text(full_text)
    metadatas = [
        {"source": pdf_path.name, "chunk_index": i}
        for i in range(len(chunks))
    ]
    logger.info(f"{pdf_path.name}: {len(reader.pages)} pages → {len(chunks)} chunks")
    return chunks, metadatas


def already_indexed(source_name: str) -> bool:
    """Check if this source PDF is already in ChromaDB."""
    collection = get_collection()
    results    = collection.get(where={"source": source_name}, limit=1)
    return len(results["ids"]) > 0


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = list(DOCS_DIR.glob("*.pdf"))

    if not pdf_files:
        logger.warning(
            f"No PDFs found in {DOCS_DIR}. "
            "Add RBI / AML / PMLA PDF files and re-run."
        )
        logger.info(
            "Tip: Download from https://www.rbi.org.in/Scripts/BS_ViewMasCirculardetails.aspx"
        )
        return

    for pdf_path in pdf_files:
        if already_indexed(pdf_path.name):
            logger.info(f"Already indexed: {pdf_path.name} — skipping.")
            continue

        texts, metadatas = pdf_to_chunks(pdf_path)
        ingest_texts(texts, metadatas)

    logger.success("Document ingestion complete ✓")


if __name__ == "__main__":
    main()
