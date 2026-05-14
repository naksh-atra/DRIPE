"""
Main evaluator for DRIPE v2.
Orchestrates ranking evaluation, explanation review, and report generation.
"""
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional, Set

from evaluation.gold_standard_builder import build_ra_gold_standard
from evaluation.ranking_metrics import compute_all_metrics, recall_at_k, mrr
from ranking.baselines.random_baseline import score_random

logger = logging.getLogger(__name__)


class MVPEvaluator:
    """Evaluation harness for DRIPE v2."""

    def __init__(self, gold_standard: Optional[List[Dict]] = None):
        self.gold_standard = gold_standard or build_ra_gold_standard()
        self.gold_set: Set[str] = {g["drug_name"].lower() for g in self.gold_standard}

    def evaluate_ranking(self, ranked_drugs: List[str]) -> Dict:
        """Evaluate ranking against gold standard."""
        ranked_lower = [d.lower().replace("drug:", "") for d in ranked_drugs]

        system_metrics = compute_all_metrics(ranked_lower, self.gold_set)

        # Random baseline
        random_scores = score_random(len(ranked_drugs))
        random_ranked = sorted(
            zip(ranked_lower, random_scores), key=lambda x: -x[1]
        )
        random_ranked_names = [r[0] for r in random_ranked]
        random_metrics = compute_all_metrics(random_ranked_names, self.gold_set)

        return {
            "evaluation_date": datetime.utcnow().isoformat(),
            "graph_version": "ra-program-v1",
            "system": system_metrics,
            "baseline_random": random_metrics,
            "known_issues": [
                "GNN evaluation deferred until graph > 1000 edges",
                "Path-count baseline not yet computed",
            ],
        }


def run_evaluation(ranked_drugs: List[str]) -> Dict:
    """Convenience function to run a full evaluation pass."""
    evaluator = MVPEvaluator()
    return evaluator.evaluate_ranking(ranked_drugs)
