"""
Gold standard builder for DRIPE v2 evaluation.
Constructs known-therapy lists from public sources.
"""
from typing import List, Dict
from ranking.novelty_classifier import KNOWN_RA_THERAPIES, ADJACENT_THERAPIES


def build_ra_gold_standard() -> List[Dict]:
    """Build gold standard of known RA therapies."""
    gold = []
    for drug in sorted(KNOWN_RA_THERAPIES):
        gold.append({
            "drug_name": drug,
            "disease": "rheumatoid arthritis",
            "disease_cui": "C0003873",
            "category": "known_indication",
        })
    for drug in sorted(ADJACENT_THERAPIES):
        gold.append({
            "drug_name": drug,
            "disease": "rheumatoid arthritis",
            "disease_cui": "C0003873",
            "category": "adjacent_offlabel",
        })
    return gold
