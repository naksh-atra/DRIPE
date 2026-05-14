"""
Candidate assembler for DRIPE v2.
Builds candidate objects from graph paths, ranking scores, retrieval, and explanation.
"""
from typing import List, Dict, Optional

from schemas.response import (
    Candidate, RankingScores, ScoreComponents, SupportingPath, RetrievedEvidence,
    CounterEvidence, Explanation,
)
from schemas.explanation import NoveltyBucket, EvidenceTier
from ranking.composite_scorer import compute_composite
from ranking.novelty_classifier import classify_novelty


def assemble_candidate(
    drug_name: str,
    drug_id: str,
    paths: List[Dict],
    graph_score: float,
    evidence_score: float,
    trial_score: float,
    learned_score: float = 0.0,
    literature: Optional[List[RetrievedEvidence]] = None,
    counter_evidence: Optional[List[CounterEvidence]] = None,
    explanation: Optional[Explanation] = None,
    trial_count: int = 0,
) -> Candidate:
    """Assemble a candidate object from pipeline outputs."""
    scores = compute_composite(graph_score, evidence_score, trial_score, learned_score)
    novelty = classify_novelty(drug_name, drug_id, trial_count)

    supporting = []
    for p in paths[:3]:
        supporting.append(SupportingPath(
            path_type="Drug-Target-Disease",
            nodes=p.get("nodes", []),
            edges=p.get("edges", []),
            path_confidence=p.get("path_confidence", 0.0),
            provenance=[p.get("source_db", "seed")],
        ))

    return Candidate(
        drug_name=drug_name,
        drug_id=drug_id,
        ranking_scores=scores,
        score_components=ScoreComponents(
            path_count=len(paths),
            avg_path_confidence=(
                sum(p.get("path_confidence", 0.0) for p in paths) / len(paths)
                if paths else 0.0
            ),
            literature_chunks=len(literature) if literature else 0,
            trial_count=trial_count,
            gnn_raw_score=learned_score,
        ),
        novelty_bucket=novelty,
        supporting_paths=supporting,
        retrieved_evidence=literature or [],
        counter_evidence=counter_evidence or [],
        explanation=explanation,
    )
