"""
LIMIT sensitivity test: PsA path traversal at 50 vs 100.
Same composite scoring, same gold standard, compare top-20 composition and recall.
"""
import asyncio, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from evaluation.gold_standard_builder import build_gold_standard
from evaluation.mvp_evaluator import MVPEvaluator, _resolve_drug, _dedup_ordered, W_GRAPH, W_TRIAL
from graph.graph_builder import GraphEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PSA_CUI = "C0395076"

async def run():
    ge = GraphEngine()
    ge.connect()

    gold = build_gold_standard(PSA_CUI)
    gold_set = {g["drug_name"].lower() for g in gold}
    logger.info(f"Gold standard: {len(gold)} therapies")

    results = {}
    for limit in [50, 100]:
        cypher = f"""
        MATCH p = (drug:Entity {{entity_type: 'Drug'}})-[:BIOREL*1..3]-(disease:Entity {{entity_id: $did}})
        RETURN
            drug.entity_id AS drug_id,
            [r in relationships(p) | {{type: r.type, confidence: r.confidence}}] AS path_edges
        ORDER BY reduce(conf = 1.0, r IN relationships(p) | conf * COALESCE(r.confidence, 0.5)) DESC
        LIMIT {limit}
        """
        raw = ge.run_cypher(cypher, {"did": PSA_CUI})

        paths = []
        for row in raw:
            paths.append({
                "drug_id": row["drug_id"],
                "edges": row["path_edges"],
                "path_confidence": sum(e["confidence"] for e in row["path_edges"]) / len(row["path_edges"]) if row["path_edges"] else 0,
            })

        ranked = [p["drug_id"] for p in paths]
        deduped = _dedup_ordered(ranked)
        resolved = [_resolve_drug(d) for d in deduped]

        path_map = {}
        for p in paths:
            did = p["drug_id"]
            if did not in path_map:
                path_map[did] = []
            path_map[did].append(p)

        trial_counts = {}
        for did in set(ranked):
            r = ge.run_cypher(
                "MATCH (n:Entity {entity_id: $eid})-[rb:BIOREL {type: 'TRIAL_INVESTIGATES'}]->() RETURN count(rb) AS c",
                {"eid": did}
            )
            trial_counts[did] = r[0]["c"] if r else 0

        evaluator = MVPEvaluator(gold, disease_cui=PSA_CUI)
        comp = evaluator.evaluate_composite_ranking(ranked, path_map, trial_counts)

        top20 = resolved[:20]
        gold_in_top20 = [r for r in top20 if r.lower() in gold_set]
        filler_in_top20 = [r for r in top20 if r.lower() not in gold_set]
        unique_drugs = len(deduped)

        results[limit] = {
            "total_paths": len(paths),
            "unique_drugs": unique_drugs,
            "raw_recall_10": comp["system_raw"].get("recall_at_10", 0),
            "raw_recall_20": comp["system_raw"].get("recall_at_20", 0),
            "composite_recall_10": comp["system_composite"].get("recall_at_10", 0),
            "composite_recall_20": comp["system_composite"].get("recall_at_20", 0),
            "gold_in_top20": gold_in_top20,
            "filler_in_top20": filler_in_top20,
            "deltas": comp["gold_deltas"],
            "top10_gold_count": sum(1 for r in resolved[:10] if r.lower() in gold_set),
        }

    print(f"\n{'='*70}")
    print(f"  LIMIT Sensitivity — PsA Composite Evaluation")
    print(f"{'='*70}")
    print(f"\n  {'Metric':30s} {'LIMIT=50':>12s} {'LIMIT=100':>12s}")
    print(f"  {'-'*54}")
    for metric in ["total_paths", "unique_drugs", "composite_recall_10", "composite_recall_20",
                   "raw_recall_10", "raw_recall_20"]:
        v50 = results[50][metric]
        v100 = results[100][metric]
        pct = f"({((v100/v50)-1)*100:+.1f}%)" if isinstance(v50, (int, float)) and v50 > 0 else ""
        print(f"  {metric:30s} {str(v50):>12s} {str(v100):>12s} {pct}")

    print(f"\n  Gold in top 20 (LIMIT=50): {results[50]['gold_in_top20']}")
    print(f"  Gold in top 20 (LIMIT=100): {results[100]['gold_in_top20']}")
    print(f"  Filler in top 20 (LIMIT=50): {len(results[50]['filler_in_top20'])}")
    print(f"  Filler in top 20 (LIMIT=100): {len(results[100]['filler_in_top20'])}")

    print(f"\n  Drug deltas at LIMIT=100:")
    deltas = results[100]["deltas"]
    print(f"  {'Drug':20s} {'RawRank':>8s} {'CompRank':>10s} {'Delta':>6s}")
    print(f"  {'-'*46}")
    for name in sorted(deltas):
        d = deltas[name]
        delta_str = f"+{d['delta']}" if d['delta'] and d['delta'] > 0 else str(d['delta']) if d['delta'] else "-"
        print(f"  {name:20s} {str(d['raw_rank']):>8s} {str(d['composite_rank']):>10s} {delta_str:>6s}")

    # Summary verdict
    comp_10_50 = results[50]["composite_recall_10"]
    comp_10_100 = results[100]["composite_recall_10"]
    comp_20_50 = results[50]["composite_recall_20"]
    comp_20_100 = results[100]["composite_recall_20"]
    print(f"\n  {'='*50}")
    print(f"  VERDICT: LIMIT 50->100 impact on composite recall")
    print(f"    Recall@10: {comp_10_50:.2f} -> {comp_10_100:.2f} ({((comp_10_100/comp_10_50)-1)*100:+.1f}%)")
    print(f"    Recall@20: {comp_20_50:.2f} -> {comp_20_100:.2f} ({((comp_20_100/comp_20_50)-1)*100:+.1f}%)")
    filler_delta = len(results[100]["filler_in_top20"]) - len(results[50]["filler_in_top20"])
    print(f"    Top-20 filler count change: {filler_delta:+d}")
    print(f"  {'='*50}")

    ge.close()

asyncio.run(run())
