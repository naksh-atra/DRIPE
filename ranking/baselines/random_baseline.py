"""
Random baseline ranker.
Returns random scores for sanity checking.
"""
import random
from typing import List


def score_random(num_candidates: int) -> List[float]:
    """Return random scores for N candidates."""
    random.seed(42)
    scores = [random.random() for _ in range(num_candidates)]
    total = sum(scores)
    return [s / total for s in scores]
