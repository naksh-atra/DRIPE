"""
Composite evaluation for SLE — with trial count, gold delta logging.
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

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SLE_CUI = "C0024141"

async def main():
    gold = build_gold_standard(SLE_CUI)
    print(f"Gold standard: {len(gold)} therapies")
    for g in gold:
        print(f"  {g['drug_name']}")
    print()

    ge = GraphEngine()
    ge.connect()
    pt = PathTraversal(ge)
    paths = await pt.get_drug_disease_paths(SLE_CUI)
    print(f"Paths found: {len(paths)}")
    print()

    ranked = [p["drug_id"] for p in paths]
    path_map = {}
    trial_counts = {}
    for p in paths:
        did = p["drug_id"]
        if did not in path_map:
            path_map[did] = []
        path_map[did].append(p)

    # Trial count: count distinct TRIAL_INVESTIGATES edges per drug
    for p in paths:
        did = p["drug_id"]
        if did not in trial_counts:
            result = ge.run_cypher(
                "MATCH (d:Entity {entity_id: $eid})-[r:BIOREL {type:'TRIAL_INVESTIGATES'}]->(t:Entity {entity_type: 'Trial'}) "
                "RETURN count(DISTINCT t) AS cnt",
                {"eid": did},
            )
            trial_counts[did] = result[0]["cnt"] if result else 0

    evaluator = MVPEvaluator(gold, disease_cui=SLE_CUI)
    results = evaluator.evaluate_composite_ranking(ranked, candidate_paths=path_map, trial_counts=trial_counts)
    ge.close()

    raw = results["system_raw"]
    comp = results["system_composite"]
    print("=== SLE Composite Evaluation ===")
    print(f"  Raw Recall@10:      {raw.get('recall_at_10', 'N/A')}")
    print(f"  Raw Recall@20:      {raw.get('recall_at_20', 'N/A')}")
    print(f"  Raw MRR:            {raw.get('mrr', 'N/A')}")
    print(f"  Composite Recall@10: {comp.get('recall_at_10', 'N/A')}")
    print(f"  Composite Recall@20: {comp.get('recall_at_20', 'N/A')}")
    print(f"  Composite MRR:       {comp.get('mrr', 'N/A')}")

    deltas = results.get("gold_deltas", {})
    print(f"\n=== Gold drug rank deltas ===")
    for name, info in sorted(deltas.items(), key=lambda x: x[1].get("composite_rank", 999)):
        print(f"  {name:30s} | raw={info.get('raw_rank','N/A'):>4} -> composite={info.get('composite_rank','N/A'):>4} "
              f"| graph={info.get('graph_score','N/A')} trial={info.get('trial_score','N/A')} ({info.get('trial_count','N/A')} trials)")

if __name__ == "__main__":
    asyncio.run(main())
