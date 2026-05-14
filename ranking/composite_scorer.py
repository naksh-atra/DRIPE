"""
Composite scorer for DRIPE v2.
Combines graph, evidence, trial, and learned scores.
"""
import logging
from typing import List, Dict, Optional
from schemas.response import RankingScores, ScoreComponents

logger = logging.getLogger(__name__)

# MVP weights — heuristic, to be validated
W_GRAPH = 0.40
W_EVIDENCE = 0.25
W_TRIAL = 0.20
W_LEARNED = 0.15


def compute_composite(
    graph_score: float,
    evidence_score: float,
    trial_score: float,
    learned_score: float = 0.0,
) -> RankingScores:
    """Compute composite score from component scores."""
    scores = RankingScores(
        graph_score=round(graph_score, 4),
        evidence_score=round(evidence_score, 4),
        trial_score=round(trial_score, 4),
        learned_score=round(learned_score, 4),
    )
    scores.composite_score = round(
        W_GRAPH * graph_score +
        W_EVIDENCE * evidence_score +
        W_TRIAL * trial_score +
        W_LEARNED * learned_score,
        4
    )
    return scores


def normalize_scores(candidates: List[Dict], score_key: str) -> None:
    """Min-max normalize a score field across candidates."""
    values = [c.get(score_key, 0.0) for c in candidates]
    mn, mx = min(values), max(values)
    rng = mx - mn
    if rng == 0:
        for c in candidates:
            c[score_key] = 0.0
    else:
        for c in candidates:
            c[score_key] = (c.get(score_key, 0.0) - mn) / rng
