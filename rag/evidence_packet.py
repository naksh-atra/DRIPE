"""
Evidence packet builder for DRIPE v2.
Assembles retrieved evidence into structured evidence packets.
"""
import logging
from typing import List, Dict, Optional
from schemas.response import RetrievedEvidence, CounterEvidence

logger = logging.getLogger(__name__)


def build_evidence_packet(
    pmid_results: List[Dict],
    trial_results: List[Dict],
) -> List[RetrievedEvidence]:
    """Build evidence packet from retrieval results."""
    seen = set()
    packet = []

    for r in pmid_results:
        identifier = r.get("pmid") or r.get("identifier", "")
        if identifier in seen:
            continue
        seen.add(identifier)
        packet.append(RetrievedEvidence(
            source_type="pubmed",
            identifier=identifier,
            title=r.get("title", ""),
            snippet=r.get("text", "")[:300],
            year=r.get("year", 0),
            relevance_score=r.get("relevance_score", 0.0),
        ))

    for r in trial_results:
        identifier = r.get("nct_id") or r.get("identifier", "")
        if identifier in seen:
            continue
        seen.add(identifier)
        packet.append(RetrievedEvidence(
            source_type="trial",
            identifier=identifier,
            title=r.get("title", ""),
            snippet=r.get("text", "")[:300],
            year=r.get("year", 0),
            relevance_score=r.get("relevance_score", 0.0),
        ))

    return packet


def check_counter_evidence(drug_name: str, disease_name: str, literature_count: int) -> List[CounterEvidence]:
    """Check for counter-evidence signals."""
    flags = []
    if literature_count == 0:
        flags.append(CounterEvidence(
            type="sparse_support",
            detail=f"No literature found for {drug_name} in {disease_name}. Evidence density is insufficient."
        ))
    return flags
