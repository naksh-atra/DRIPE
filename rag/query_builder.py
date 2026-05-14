"""
Candidate-aware query builder for DRIPE v2 RAG.
Constructs targeted retrieval queries from graph path data.
"""
from typing import List, Optional


def build_mechanism_query(drug: str, disease: str, targets: Optional[List[str]] = None) -> str:
    """Build a mechanism-focused retrieval query."""
    parts = [drug, disease]
    if targets:
        parts.extend(targets[:3])
    parts.extend(["mechanism", "pathway"])
    return " ".join(parts)


def build_trial_query(drug: str, disease: str) -> str:
    """Build a trial-focused retrieval query."""
    return f"{drug} {disease} trial"


def build_repurposing_query(drug: str, disease: str) -> str:
    """Build a repurposing-focused retrieval query."""
    return f"{drug} {disease} repurposing repositioning"


def build_candidate_queries(drug: str, disease: str, targets: Optional[List[str]] = None) -> List[str]:
    """Generate all retrieval queries for a candidate."""
    return [
        build_mechanism_query(drug, disease, targets),
        build_trial_query(drug, disease),
        build_repurposing_query(drug, disease),
    ]
