"""
RAG retriever for DRIPE v2.
Candidate-aware retrieval with evidence packet assembly.
"""
import logging
from typing import List, Dict, Optional

from rag.embedder import get_embedder
from rag.vectorstore import get_vector_store
from rag.query_builder import build_candidate_queries
from rag.evidence_packet import build_evidence_packet, check_counter_evidence
from schemas.response import RetrievedEvidence, CounterEvidence

logger = logging.getLogger(__name__)


class Retriever:
    """RAG retriever for DRIPE v2."""

    def __init__(self):
        self.embedder = None
        self.vectorstore = None

    def _initialize(self):
        if self.embedder is None:
            self.embedder = get_embedder()
        if self.vectorstore is None:
            self.vectorstore = get_vector_store()

    def retrieve_for_candidate(
        self,
        drug_name: str,
        disease_name: str,
        targets: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> List[Dict]:
        """Retrieve evidence for a single candidate using candidate-aware queries."""
        self._initialize()

        queries = build_candidate_queries(drug_name, disease_name, targets)
        seen_pmids = set()
        all_results = []

        for query in queries:
            query_embedding = self.embedder.embed_text(query)
            results = self.vectorstore.search(query_embedding, top_k)
            for r in results:
                pmid = r.get("pmid") or r.get("identifier", "")
                if pmid not in seen_pmids:
                    seen_pmids.add(pmid)
                    all_results.append(r)

        return all_results[:top_k * 2]

    async def retrieve_context(
        self, drug_name: str, disease_name: str, top_k: int = 5
    ) -> List[Dict]:
        """Async wrapper for backwards compatibility."""
        return self.retrieve_for_candidate(drug_name, disease_name, top_k=top_k)


_singleton: Retriever = None


def get_retriever() -> Retriever:
    global _singleton
    if _singleton is None:
        _singleton = Retriever()
    return _singleton
