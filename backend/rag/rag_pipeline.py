"""
rag_pipeline.py
───────────────
Location : backend/rag/rag_pipeline.py
Purpose  : Initialize ChromaDB collection, embed + index PDF documents,
           and expose a rag_query() function for evidence retrieval.

Run ingest: python backend/rag/ingest_docs.py
Connects to: evidence_agent.py, api.py (chat endpoint)
"""

import os
import uuid
from pathlib import Path
from loguru import logger
from functools import lru_cache

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
CHROMA_DIR      = Path(os.getenv("CHROMA_DIR", "backend/rag/chroma_db"))
COLLECTION_NAME = "rbi_aml_guidelines"
EMBED_MODEL     = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# ── Singletons ────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    logger.info(f"Loading embedding model: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def _get_chroma_client() -> chromadb.Client:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    logger.info(f"ChromaDB client initialized at {CHROMA_DIR}")
    return client


def get_collection():
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── Ingest ────────────────────────────────────────────────────────────────────
def ingest_texts(texts: list[str], metadatas: list[dict]):
    """
    Embed and store text chunks into ChromaDB.

    Parameters
    ----------
    texts     : list of text chunks
    metadatas : list of dicts with at least {"source": str}
    """
    model      = _get_embedding_model()
    collection = get_collection()

    logger.info(f"Embedding {len(texts)} chunks …")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    ids = [str(uuid.uuid4()) for _ in texts]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.success(f"Ingested {len(texts)} chunks into '{COLLECTION_NAME}'.")


# ── Query ─────────────────────────────────────────────────────────────────────
def rag_query(query: str, top_k: int = 3) -> list[dict]:
    """
    Semantic search over the ChromaDB collection.

    Returns
    -------
    list of dicts: {id, text, source, score}
    """
    model      = _get_embedding_model()
    collection = get_collection()

    # Check if collection has any documents
    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty. Run ingest_docs.py first.")
        return _fallback_guidelines(query)

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "id":     results["ids"][0][i],
            "text":   doc,
            "source": results["metadatas"][0][i].get("source", "Unknown"),
            "score":  round(1 - results["distances"][0][i], 4),  # cosine similarity
        })

    return output


# ── Fallback (hardcoded RBI/AML snippets when no PDFs indexed) ────────────────
def _fallback_guidelines(query: str) -> list[dict]:
    """Return built-in RBI/AML guideline snippets when ChromaDB is empty."""
    guidelines = [
        {
            "id":     "rbi-str-001",
            "text":   (
                "As per RBI Master Direction on KYC (2016, updated 2023), Reporting "
                "Entities (RE) are required to file Suspicious Transaction Reports (STR) "
                "with the Financial Intelligence Unit - India (FIU-IND) within 7 working "
                "days of forming a suspicion. Transactions that appear to be structured "
                "to avoid reporting thresholds must be reported immediately."
            ),
            "source": "RBI KYC Master Direction 2023 (Built-in)",
            "score":  0.85,
        },
        {
            "id":     "pmla-001",
            "text":   (
                "Under the Prevention of Money Laundering Act (PMLA) 2002 and its "
                "Amendment Rules 2023, any cash transaction above ₹10 lakhs or its "
                "equivalent in foreign currency, and all suspicious transactions "
                "regardless of amount, must be reported to FIU-IND. Failure to report "
                "can result in penalties up to ₹1 lakh per violation."
            ),
            "source": "PMLA Rules 2023 (Built-in)",
            "score":  0.82,
        },
        {
            "id":     "rbi-aml-002",
            "text":   (
                "RBI Circular RBI/2023-24/73 on AML/CFT: Banks must implement robust "
                "transaction monitoring systems to detect unusual patterns including: "
                "sudden large transfers inconsistent with customer profile, rapid "
                "movement of funds through multiple accounts (layering), and zero-balance "
                "destination accounts receiving large transfers. Enhanced Due Diligence "
                "(EDD) is mandatory for high-risk customers."
            ),
            "source": "RBI AML/CFT Circular 2023 (Built-in)",
            "score":  0.79,
        },
        {
            "id":     "fatf-001",
            "text":   (
                "FATF Recommendation 20 requires countries to ensure that financial "
                "institutions report suspicious transactions to the FIU when they "
                "suspect or have reasonable grounds to suspect that funds are the "
                "proceeds of criminal activity or are related to terrorist financing. "
                "India is a FATF member and must comply with these standards."
            ),
            "source": "FATF Recommendations (Built-in)",
            "score":  0.75,
        },
    ]
    return guidelines
