"""
Explanation review module for DRIPE v2 evaluation.
Manual review protocol for top candidate explanations.
"""
from typing import List, Dict, Optional
from schemas.response import Candidate


REVIEW_CRITERIA = [
    "graph_grounding",
    "literature_match",
    "explanation_accuracy",
    "uncertainty_appropriateness",
    "clinical_safety",
]


def review_template(candidates: List[Candidate]) -> Dict:
    """Generate a manual review worksheet for top candidates."""
    worksheet = {
        "review_date": "",
        "reviewer": "",
        "candidates": [],
    }
    for c in candidates[:5]:
        worksheet["candidates"].append({
            "drug_name": c.drug_name,
            "rank": None,
            "graph_grounding": {"rating": "", "notes": ""},
            "literature_match": {"rating": "", "notes": ""},
            "explanation_accuracy": {"rating": "", "notes": ""},
            "uncertainty_appropriateness": {"rating": "", "notes": ""},
            "clinical_safety": {"rating": "pass", "notes": ""},
        })
    return worksheet
