"""
Ranking metrics for DRIPE v2 evaluation.
Recall@K, MRR, and novelty-aware metrics.
"""
from typing import List, Dict, Set


def recall_at_k(ranked: List[str], gold_set: Set[str], k: int) -> float:
    """Compute recall@K."""
    if not gold_set:
        return 0.0
    top_k = set(ranked[:k])
    hits = len(top_k & gold_set)
    return hits / len(gold_set)


def mrr(ranked: List[str], gold_set: Set[str]) -> float:
    """Compute mean reciprocal rank."""
    for i, drug in enumerate(ranked):
        if drug in gold_set:
            return 1.0 / (i + 1)
    return 0.0


def compute_all_metrics(
    ranked_drugs: List[str],
    gold_set: Set[str],
) -> Dict:
    """Compute all primary metrics."""
    return {
        "recall_at_10": round(recall_at_k(ranked_drugs, gold_set, 10), 4),
        "recall_at_20": round(recall_at_k(ranked_drugs, gold_set, 20), 4),
        "mrr": round(mrr(ranked_drugs, gold_set), 4),
        "num_gold": len(gold_set),
        "num_candidates": len(ranked_drugs),
    }
