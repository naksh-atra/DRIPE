import logging
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple

from evaluation.gold_standard_builder import build_gold_standard
from evaluation.ranking_metrics import compute_all_metrics
from ranking.baselines.random_baseline import score_random
from ranking.baselines.common_neighbor import score_by_common_neighbors
from ranking.baselines.weighted_path import score_by_weighted_paths
from config.ra_therapies import get_known_indications as get_ra_known, get_adjacent_therapies as get_ra_adj, get_chembl_id_map as get_ra_chembl
from config.adjacent_therapies import get_known_indications, get_adjacent_therapies, get_chembl_id_map

W_GRAPH = 0.40
W_EVIDENCE = 0.25
W_TRIAL = 0.20
W_LEARNED = 0.15

logger = logging.getLogger(__name__)

_DRUG_ID_MAP = None

def _build_id_map() -> Dict[str, str]:
    global _DRUG_ID_MAP
    if _DRUG_ID_MAP is not None:
        return _DRUG_ID_MAP
    _DRUG_ID_MAP = {}

    all_known = {}
    all_adjacent = {}
    all_chembl = {}
    all_known.update(get_ra_known())
    all_adjacent.update(get_ra_adj())
    all_chembl.update(get_ra_chembl())
    for cui in ["C0024141", "C0395076", "C0036075"]:
        all_known.update(get_known_indications(cui))
        all_adjacent.update(get_adjacent_therapies(cui))
        all_chembl.update(get_chembl_id_map(cui))

    for name in all_known:
        _DRUG_ID_MAP[name.lower()] = name
        cid = all_known[name]
        if cid:
            _DRUG_ID_MAP[cid.lower()] = name
            _DRUG_ID_MAP[cid.upper()] = name
        for prefix in ["RA_THERAPY_", "PSA_THERAPY_", "SLE_THERAPY_", "SJOGREN_THERAPY_"]:
            _DRUG_ID_MAP[f"{prefix}{name}".lower()] = name

    for name in all_adjacent:
        _DRUG_ID_MAP[name.lower()] = name
        cid = all_adjacent[name]
        if cid:
            _DRUG_ID_MAP[cid.lower()] = name
            _DRUG_ID_MAP[cid.upper()] = name
    return _DRUG_ID_MAP

def _resolve_drug(drug_str: str) -> str:
    clean = drug_str.lower().replace("drug:", "")
    m = _build_id_map()
    return m.get(clean, clean)

def _dedup_ordered(items: List[str]) -> List[str]:
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))]

class MVPEvaluator:
    def __init__(self, gold_standard: Optional[List[Dict]] = None, disease_cui: str = "C0003873"):
        self.disease_cui = disease_cui
        self.gold_standard = gold_standard or build_gold_standard(disease_cui)
        self.gold_set: Set[str] = {g["drug_name"].lower() for g in self.gold_standard}

    def evaluate_ranking(
        self,
        ranked_drugs: List[str],
        candidate_paths: Optional[Dict[str, List[Dict]]] = None,
    ) -> Dict:
        deduped = _dedup_ordered(ranked_drugs)
        ranked_resolved = [_resolve_drug(d) for d in deduped]

        system_metrics = compute_all_metrics(ranked_resolved, self.gold_set)

        random_scores = score_random(len(ranked_drugs))
        random_ranked = sorted(zip(ranked_resolved, random_scores), key=lambda x: -x[1])
        random_ranked_names = [r[0] for r in random_ranked]
        random_metrics = compute_all_metrics(random_ranked_names, self.gold_set)

        path_metrics = {}
        if candidate_paths:
            path_scores = []
            for drug in ranked_resolved:
                drug_id = f"CHEMBL{drug.replace('chembl', '')}" if drug.startswith("chembl") else drug
                paths = candidate_paths.get(drug, candidate_paths.get(drug_id, []))
                path_scores.append(score_by_weighted_paths(paths))
            path_ranked = sorted(zip(ranked_resolved, path_scores), key=lambda x: -x[1])
            path_ranked_names = [r[0] for r in path_ranked]
            path_metrics = compute_all_metrics(path_ranked_names, self.gold_set)

        cn_metrics = {}
        if candidate_paths:
            cn_scores = []
            for drug in ranked_resolved:
                drug_id = f"CHEMBL{drug.replace('chembl', '')}" if drug.startswith("chembl") else drug
                paths = candidate_paths.get(drug, candidate_paths.get(drug_id, []))
                cn_scores.append(score_by_common_neighbors(drug, self.disease_cui, paths))
            cn_ranked = sorted(zip(ranked_resolved, cn_scores), key=lambda x: -x[1])
            cn_ranked_names = [r[0] for r in cn_ranked]
            cn_metrics = compute_all_metrics(cn_ranked_names, self.gold_set)

        return {
            "evaluation_date": datetime.utcnow().isoformat(),
            "disease_cui": self.disease_cui,
            "gold_standard_size": len(self.gold_standard),
            "graph_version": "ra-program-v1",
            "system": system_metrics,
            "baseline_random": random_metrics,
            "baseline_path_count": path_metrics or {"status": "skipped_no_path_data"},
            "baseline_common_neighbor": cn_metrics or {"status": "skipped_no_path_data"},
            "known_issues": [
                "GNN evaluation deferred until graph > 1000 edges",
            ],
        }

    def evaluate_composite_ranking(
        self,
        ranked_drugs: List[str],
        candidate_paths: Optional[Dict[str, List[Dict]]] = None,
        trial_counts: Optional[Dict[str, int]] = None,
    ) -> Dict:
        deduped = _dedup_ordered(ranked_drugs)
        ranked_resolved = [_resolve_drug(d) for d in deduped]

        raw_metrics = compute_all_metrics(ranked_resolved, self.gold_set)

        trial_counts = trial_counts or {}

        composite_items = []
        for drug_id, resolved_name in zip(deduped, ranked_resolved):
            paths = (candidate_paths or {}).get(drug_id, [])
            graph_score = max((p.get("path_confidence", 0.5) for p in paths), default=0.5)
            tcount = trial_counts.get(drug_id, 0)
            tscore = min(tcount / 10.0, 1.0)
            composite = W_GRAPH * graph_score + W_TRIAL * tscore
            composite_items.append((resolved_name, composite, graph_score, tscore, tcount))

        composite_items.sort(key=lambda x: -x[1])
        composite_ranked = [item[0] for item in composite_items]
        composite_metrics = compute_all_metrics(composite_ranked, self.gold_set)

        deltas = {}
        for resolved_name, _, gs, ts, tc in composite_items:
            if resolved_name.lower() in self.gold_set:
                raw_pos = next((i+1 for i, r in enumerate(ranked_resolved) if r == resolved_name), None)
                comp_pos = next((i+1 for i, r in enumerate(composite_ranked) if r == resolved_name), None)
                deltas[resolved_name] = {
                    "raw_rank": raw_pos,
                    "composite_rank": comp_pos,
                    "graph_score": round(gs, 4),
                    "trial_score": round(ts, 4),
                    "trial_count": tc,
                    "composite_score": round(W_GRAPH * gs + W_TRIAL * ts, 4),
                    "delta": (comp_pos - raw_pos) if raw_pos and comp_pos else None,
                }

        return {
            "evaluation_date": datetime.utcnow().isoformat(),
            "disease_cui": self.disease_cui,
            "gold_standard_size": len(self.gold_standard),
            "graph_version": "ra-program-v1",
            "system_raw": raw_metrics,
            "system_composite": composite_metrics,
            "gold_deltas": deltas,
            "known_issues": [
                "GNN deferred (0.0 learned_score); evidence_score omitted (no RAG in eval)",
            ],
        }
