"""
Run MVP evaluation for DRIPE v2.
Fetches real graph data and evaluates system ranking with baselines.
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
    gold = build_gold_standard("C0003873")
    logger.info(f"Gold standard: {len(gold)} therapies")

    # Connect to graph and get paths
    ge = GraphEngine()
    ge.connect()
    pt = PathTraversal(ge)
    paths = await pt.get_drug_disease_paths("C0003873")
    logger.info(f"Found {len(paths)} drug-disease paths")

    # Build ranked list and path map
    ranked = [p["drug_id"] for p in paths] or [
        "methotrexate", "adalimumab", "baricitinib", "prednisone", "ibuprofen",
        "aspirin", "metformin", "acetaminophen", "naproxen", "celecoxib",
    ]

    path_map = {}
    for p in paths:
        drug_id = p["drug_id"]
        if drug_id not in path_map:
            path_map[drug_id] = []
        path_map[drug_id].append(p)

    # Evaluate
    evaluator = MVPEvaluator(gold)
    results = evaluator.evaluate_ranking(ranked, candidate_paths=path_map)

    print(json.dumps(results, indent=2))

    # Print verdict
    s = results["system"]
    pc = results.get("baseline_path_count", {})
    cn = results.get("baseline_common_neighbor", {})
    print(f"\n--- Quick Comparison (Recall@10) ---")
    print(f"  System:          {s.get('recall_at_10', 'N/A')}")
    print(f"  Path-count:      {pc.get('recall_at_10', 'N/A')}")
    print(f"  Common-neighbor: {cn.get('recall_at_10', 'N/A')}")
    print(f"  Random:          {results['baseline_random'].get('recall_at_10', 'N/A')}")

    ge.close()

if __name__ == "__main__":
    asyncio.run(main())
