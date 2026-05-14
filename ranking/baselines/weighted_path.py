"""
Weighted path count baseline ranker.
Scores candidates by summing confidence-weighted path scores.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

DECAY_PER_HOP = 0.7


def score_by_weighted_paths(paths: List[Dict]) -> float:
    """Score drug-disease pair by weighted path count."""
    if not paths:
        return 0.0

    total = 0.0
    for p in paths:
        conf = p.get("path_confidence", 0.5)
        length = len(p.get("nodes", [])) - 1
        weighted = conf * (DECAY_PER_HOP ** max(length - 1, 0))
        total += weighted

    return min(total / 5.0, 1.0)
