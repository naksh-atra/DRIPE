"""
Novelty classifier for DRIPE v2.
Labels candidates by their novelty status using the RA therapy registry.
"""
import logging
from typing import Optional, Set

from schemas.explanation import NoveltyBucket
from config.ra_therapies import get_known_indications, get_adjacent_therapies, get_chembl_id_map

logger = logging.getLogger(__name__)

_KNOWN_MAP = None
_ADJACENT_MAP = None
_CHEMBL_NAME_MAP = None


def _load():
    global _KNOWN_MAP, _ADJACENT_MAP, _CHEMBL_NAME_MAP
    if _KNOWN_MAP is None:
        _KNOWN_MAP = get_known_indications()
        _ADJACENT_MAP = get_adjacent_therapies()
        _CHEMBL_NAME_MAP = get_chembl_id_map()
        # Also build reverse map (chembl_id -> name)
        _CHEMBL_NAME_MAP.update({v: k for k, v in _CHEMBL_NAME_MAP.items()})
        # Add registry IDs to the name map
        for name, cid in _KNOWN_MAP.items():
            if cid:
                _CHEMBL_NAME_MAP[cid.lower()] = name
                _CHEMBL_NAME_MAP[cid.upper()] = name
        for name, cid in _ADJACENT_MAP.items():
            if cid:
                _CHEMBL_NAME_MAP[cid.lower()] = name
                _CHEMBL_NAME_MAP[cid.upper()] = name


def classify_novelty(drug_name: str, drug_id: str, trial_count: int) -> NoveltyBucket:
    """Classify a candidate drug into a novelty bucket."""
    _load()

    clean = drug_name.lower().replace("drug:", "")

    # Check by name directly
    if clean in _KNOWN_MAP:
        return NoveltyBucket.KNOWN_INDICATION
    if clean in _ADJACENT_MAP:
        return NoveltyBucket.ADJACENT_OFFLABEL

    # Check by ChEMBL ID -> name resolution
    resolved = _CHEMBL_NAME_MAP.get(clean) or _CHEMBL_NAME_MAP.get(clean.upper())
    if resolved:
        if resolved in _KNOWN_MAP:
            return NoveltyBucket.KNOWN_INDICATION
        if resolved in _ADJACENT_MAP:
            return NoveltyBucket.ADJACENT_OFFLABEL

    if trial_count > 0:
        return NoveltyBucket.TRIAL_EXPLORED

    return NoveltyBucket.EXPLORATORY
