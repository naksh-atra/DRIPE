"""
PubMed indexer for DRIPE v2 RAG.
Indexes RA-relevant PubMed abstracts into FAISS.
"""
import logging
from typing import List, Dict, Optional
from rag.vectorstore import get_vector_store
from rag.embedder import get_embedder

logger = logging.getLogger(__name__)


CHUNK_SIZE = 200
CHUNK_OVERLAP = 20


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = " ".join(words[i:i + size])
        if len(chunk) > 50:
            chunks.append(chunk)
    return chunks


def index_abstracts(articles: List[Dict]) -> int:
    """Index PubMed abstracts into FAISS."""
    embedder = get_embedder()
    store = get_vector_store()

    all_chunks = []
    all_metadata = []

    for article in articles:
        pmid = article.get("pmid", "unknown")
        abstract = article.get("abstract", "")
        if not abstract:
            continue

        chunks = chunk_text(abstract)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadata.append({
                "pmid": pmid,
                "chunk_text": chunk,
                "year": article.get("year", 2023),
                "source_type": "pubmed",
            })

    if not all_chunks:
        logger.warning("No chunks to index")
        return 0

    logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
    embeddings = embedder.embed_batch(all_chunks)
    store.add_chunks(embeddings, all_metadata)
    store.save()

    logger.info(f"Indexed {len(all_chunks)} PubMed chunks")
    return len(all_chunks)
