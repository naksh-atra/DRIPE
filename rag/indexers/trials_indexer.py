"""
ClinicalTrials.gov indexer for DRIPE v2 RAG.
Indexes RA-relevant trial summaries into FAISS.
"""
import logging
from typing import List, Dict
from rag.vectorstore import get_vector_store
from rag.embedder import get_embedder

logger = logging.getLogger(__name__)


def index_trials(trials: List[Dict]) -> int:
    """Index clinical trial summaries into FAISS."""
    embedder = get_embedder()
    store = get_vector_store()

    all_chunks = []
    all_metadata = []

    for trial in trials:
        nct_id = trial.get("nct_id", "unknown")
        title = trial.get("title", "")
        summary = f"{title} | {trial.get('conditions', '')} | {trial.get('phase', '')} | {trial.get('status', '')}"
        if not title:
            continue

        all_chunks.append(summary)
        all_metadata.append({
            "pmid": nct_id,
            "chunk_text": summary,
            "year": 2023,
            "source_type": "trial",
        })

    if not all_chunks:
        logger.warning("No trial chunks to index")
        return 0

    logger.info(f"Generating embeddings for {len(all_chunks)} trial summaries")
    embeddings = embedder.embed_batch(all_chunks)
    store.add_chunks(embeddings, all_metadata)
    store.save()

    logger.info(f"Indexed {len(all_chunks)} trial summaries")
    return len(all_chunks)
