"""
Gold standard builder for DRIPE v2 evaluation.
Constructs known-therapy lists from the RA therapy registry.
"""
from typing import List, Dict
from config.ra_therapies import get_known_indications, get_adjacent_therapies


def build_ra_gold_standard() -> List[Dict]:
    """Build gold standard of known RA therapies from registry."""
    gold = []
    for name in sorted(get_known_indications()):
        gold.append({
            "drug_name": name,
            "disease": "rheumatoid arthritis",
            "disease_cui": "C0003873",
            "category": "known_indication",
        })
    for name in sorted(get_adjacent_therapies()):
        gold.append({
            "drug_name": name,
            "disease": "rheumatoid arthritis",
            "disease_cui": "C0003873",
            "category": "adjacent_offlabel",
        })
    return gold
