"""
Novelty classifier for DRIPE v2.
Labels candidates by their novelty status.
"""
import logging
from typing import List, Dict, Set

from schemas.explanation import NoveltyBucket

logger = logging.getLogger(__name__)

# Curated list of known RA therapies for novelty classification
KNOWN_RA_THERAPIES: Set[str] = {
    "methotrexate", "adalimumab", "etanercept", "infliximab", "rituximab",
    "tocilizumab", "baricitinib", "tofacitinib", "abatacept", "sulfasalazine",
    "leflunomide", "hydroxychloroquine", "certolizumab", "golimumab", "sarilumab",
    "upadacitinib", "filgotinib", "anakinra", "prednisone", "methylprednisolone",
    "cyclosporine", "azathioprine", "penicillamine", "mycophenolate",
}

# Adjacent disease therapies (approved for PsA, SLE, but not RA)
ADJACENT_THERAPIES: Set[str] = {
    "ustekinumab", "secukinumab", "ixekizumab", "belimumab", "apremilast",
}


def classify_novelty(drug_name: str, drug_id: str, trial_count: int) -> NoveltyBucket:
    """Classify a candidate drug into a novelty bucket."""
    name_lower = drug_name.lower().replace("drug:", "")

    if name_lower in KNOWN_RA_THERAPIES:
        return NoveltyBucket.KNOWN_INDICATION

    if name_lower in ADJACENT_THERAPIES:
        return NoveltyBucket.ADJACENT_OFFLABEL

    if trial_count > 0:
        return NoveltyBucket.TRIAL_EXPLORED

    return NoveltyBucket.EXPLORATORY
