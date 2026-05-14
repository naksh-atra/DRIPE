"""
Run MVP evaluation for DRIPE v2.
"""
import json
import logging
from evaluation.gold_standard_builder import build_ra_gold_standard
from evaluation.mvp_evaluator import MVPEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample ranked drugs for testing (replace with real system output later)
SAMPLE_RANKED = [
    "methotrexate", "adalimumab", "baricitinib", "prednisone", "ibuprofen",
    "aspirin", "metformin", "acetaminophen", "naproxen", "celecoxib",
]


if __name__ == "__main__":
    gold = build_ra_gold_standard()
    logger.info(f"Gold standard: {len(gold)} therapies")

    evaluator = MVPEvaluator(gold)
    results = evaluator.evaluate_ranking(SAMPLE_RANKED)

    print(json.dumps(results, indent=2))
