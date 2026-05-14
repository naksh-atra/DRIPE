"""
Main evaluator for DRIPE v2.
Orchestrates ranking evaluation, explanation review, and report generation.
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set

from evaluation.gold_standard_builder import build_ra_gold_standard
from evaluation.ranking_metrics import compute_all_metrics
from ranking.baselines.random_baseline import score_random
from ranking.baselines.common_neighbor import score_by_common_neighbors
from ranking.baselines.weighted_path import score_by_weighted_paths

logger = logging.getLogger(__name__)


class MVPEvaluator:
    """Evaluation harness for DRIPE v2."""

    def __init__(self, gold_standard: Optional[List[Dict]] = None):
        self.gold_standard = gold_standard or build_ra_gold_standard()
        self.gold_set: Set[str] = {g["drug_name"].lower() for g in self.gold_standard}

    def evaluate_ranking(
        self,
        ranked_drugs: List[str],
        candidate_paths: Optional[Dict[str, List[Dict]]] = None,
    ) -> Dict:
        """Evaluate ranking against gold standard with all baselines."""
        ranked_lower = [d.lower().replace("drug:", "") for d in ranked_drugs]

        system_metrics = compute_all_metrics(ranked_lower, self.gold_set)

        # Random baseline
        random_scores = score_random(len(ranked_drugs))
        random_ranked = sorted(
            zip(ranked_lower, random_scores), key=lambda x: -x[1]
        )
        random_ranked_names = [r[0] for r in random_ranked]
        random_metrics = compute_all_metrics(random_ranked_names, self.gold_set)

        # Path-count baseline
        path_metrics = {}
        if candidate_paths:
            path_scores = []
            for drug in ranked_lower:
                drug_id = f"CHEMBL{drug.replace('chembl', '')}" if drug.startswith("chembl") else drug
                paths = candidate_paths.get(drug, candidate_paths.get(drug_id, []))
                path_scores.append(score_by_weighted_paths(paths))

            path_ranked = sorted(
                zip(ranked_lower, path_scores), key=lambda x: -x[1]
            )
            path_ranked_names = [r[0] for r in path_ranked]
            path_metrics = compute_all_metrics(path_ranked_names, self.gold_set)

        # Common-neighbor baseline
        cn_metrics = {}
        if candidate_paths:
            cn_scores = []
            for drug in ranked_lower:
                drug_id = f"CHEMBL{drug.replace('chembl', '')}" if drug.startswith("chembl") else drug
                paths = candidate_paths.get(drug, candidate_paths.get(drug_id, []))
                cn_scores.append(score_by_common_neighbors(drug, "C0003873", paths))

            cn_ranked = sorted(
                zip(ranked_lower, cn_scores), key=lambda x: -x[1]
            )
            cn_ranked_names = [r[0] for r in cn_ranked]
            cn_metrics = compute_all_metrics(cn_ranked_names, self.gold_set)

        return {
            "evaluation_date": datetime.utcnow().isoformat(),
            "graph_version": "ra-program-v1",
            "system": system_metrics,
            "baseline_random": random_metrics,
            "baseline_path_count": path_metrics or {"status": "skipped_no_path_data"},
            "baseline_common_neighbor": cn_metrics or {"status": "skipped_no_path_data"},
            "known_issues": [
                "GNN evaluation deferred until graph > 1000 edges",
            ],
        }
