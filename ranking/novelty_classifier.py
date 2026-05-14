"""
Novelty classifier for DRIPE v2.
Labels candidates by their novelty status.
"""
import json
import logging
from pathlib import Path
from typing import Set

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

ADJACENT_THERAPIES: Set[str] = {
    "ustekinumab", "secukinumab", "ixekizumab", "belimumab", "apremilast",
}

_CHEMBL_NAME_MAP = None


def _load_name_map() -> dict:
    global _CHEMBL_NAME_MAP
    if _CHEMBL_NAME_MAP is None:
        path = Path(__file__).parent.parent / "data" / "chembl_id_name_map.json"
        if path.exists():
            with open(path) as f:
                _CHEMBL_NAME_MAP = json.load(f)
        else:
            _CHEMBL_NAME_MAP = {}
    return _CHEMBL_NAME_MAP


def classify_novelty(drug_name: str, drug_id: str, trial_count: int) -> NoveltyBucket:
    """Classify a candidate drug into a novelty bucket."""
    clean_name = drug_name.lower().replace("drug:", "")

    # Check by name
    if clean_name in KNOWN_RA_THERAPIES:
        return NoveltyBucket.KNOWN_INDICATION
    if clean_name in ADJACENT_THERAPIES:
        return NoveltyBucket.ADJACENT_OFFLABEL

    # Check by ChEMBL ID via name map
    name_map = _load_name_map()
    if clean_name in name_map:
        mapped = name_map[clean_name].lower()
        if mapped in KNOWN_RA_THERAPIES:
            return NoveltyBucket.KNOWN_INDICATION
        if mapped in ADJACENT_THERAPIES:
            return NoveltyBucket.ADJACENT_OFFLABEL

    if trial_count > 0:
        return NoveltyBucket.TRIAL_EXPLORED

    return NoveltyBucket.EXPLORATORY
