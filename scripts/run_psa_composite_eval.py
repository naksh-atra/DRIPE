"""
Evaluate PsA with composite ranking (graph + trial scores).
Logs per-drug rank deltas and compares raw vs composite metrics.
"""
import json, asyncio, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from evaluation.gold_standard_builder import build_gold_standard
from evaluation.mvp_evaluator import MVPEvaluator
from graph.graph_builder import GraphEngine
from graph.path_traversal import PathTraversal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    cui = "C0395076"
    name = "PsA"

    gold = build_gold_standard(cui)
    logger.info(f"Gold standard: {len(gold)} therapies")

    ge = GraphEngine()
    ge.connect()
    pt = PathTraversal(ge)
    paths = await pt.get_drug_disease_paths(cui)
    logger.info(f"Found {len(paths)} drug-disease paths")

    ranked = [p["drug_id"] for p in paths]
    if not ranked:
        ranked = ["methotrexate", "adalimumab"]

    path_map = {}
    for p in paths:
        did = p["drug_id"]
        if did not in path_map:
            path_map[did] = []
        path_map[did].append(p)

    trial_counts = {}
    drug_ids = list(set(ranked))
    for did in drug_ids:
        r = ge.run_cypher(
            "MATCH (n:Entity {entity_id: $eid})-[rb:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(rb) AS c",
            {"eid": did}
        )
        trial_counts[did] = r[0]["c"] if r else 0

    evaluator = MVPEvaluator(gold, disease_cui=cui)
    results = evaluator.evaluate_composite_ranking(ranked, path_map, trial_counts)

    raw = results["system_raw"]
    comp = results["system_composite"]
    print(f"\n=== {name} Composite Evaluation ===")
    print(f"  Raw Recall@10:      {raw.get('recall_at_10', 'N/A')}")
    print(f"  Composite Recall@10: {comp.get('recall_at_10', 'N/A')}")
    print(f"  Raw Recall@20:      {raw.get('recall_at_20', 'N/A')}")
    print(f"  Composite Recall@20: {comp.get('recall_at_20', 'N/A')}")
    print(f"  Raw MRR:            {raw.get('mrr', 'N/A')}")
    print(f"  Composite MRR:      {comp.get('mrr', 'N/A')}")

    deltas = results.get("gold_deltas", {})
    print(f"\n  Gold drug rank deltas (raw -> composite):")
    print(f"  {'Drug':20s} {'RawRank':>8s} {'CompRank':>10s} {'Delta':>6s} {'GraphSc':>8s} {'TrialSc':>8s} {'TrialCt':>7s}")
    print(f"  {'-'*68}")
    for name in sorted(deltas):
        d = deltas[name]
        delta_str = f"+{d['delta']}" if d['delta'] and d['delta'] > 0 else str(d['delta']) if d['delta'] else "N/A"
        print(f"  {name:20s} {str(d['raw_rank']):>8s} {str(d['composite_rank']):>10s} {delta_str:>6s} {d['graph_score']:>8.4f} {d['trial_score']:>8.4f} {d['trial_count']:>7d}")

    ge.close()

if __name__ == "__main__":
    asyncio.run(main())
