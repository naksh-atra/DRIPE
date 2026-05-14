"""
Entity ID mapper for DRIPE ingestion normalization.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Mapping of common source-specific IDs to canonical CUI codes
DISEASE_CUI_MAP: Dict[str, str] = {
    "C0003873": "C0003873",
    "rheumatoid arthritis": "C0003873",
    "RA": "C0003873",
    "C0024141": "C0024141",
    "lupus": "C0024141",
    "systemic lupus erythematosus": "C0024141",
    "SLE": "C0024141",
    "C0395076": "C0395076",
    "psoriatic arthritis": "C0395076",
    "PsA": "C0395076",
    "C0036075": "C0036075",
    "sjogren": "C0036075",
    "sjogren syndrome": "C0036075",
}


def map_to_cui(source_id: str, source_type: str = "disease") -> Optional[str]:
    """Map a source identifier to a canonical CUI."""
    key = source_id.strip().lower()
    for alias, cui in DISEASE_CUI_MAP.items():
        if alias.lower() == key:
            return cui
    return None


def normalize_entity_id(raw_id: str, source_db: str) -> str:
    """Normalize an entity ID based on source database."""
    raw_id = raw_id.strip()
    if source_db == "chembl":
        return raw_id.upper()
    if source_db == "clinicaltrials":
        return raw_id.upper()
    return raw_id
