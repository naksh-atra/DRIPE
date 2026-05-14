"""
Common-neighbor baseline ranker.
Scores candidates by counting shared targets between drug and disease.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def score_by_common_neighbors(drug_id: str, disease_id: str, paths: List[Dict]) -> float:
    """Score a drug-disease pair by shared target count."""
    if not paths:
        return 0.0
    target_count = sum(1 for p in paths if "Target" in str(p.get("nodes", [])))
    return min(target_count / 10.0, 1.0)
