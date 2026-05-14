"""
RA-focused ChEMBL loader.
Filters ChEMBL data to targets and drugs relevant to rheumatoid arthritis.
"""
import logging
from typing import List, Dict
from ingestion.chembl_connector import get_chembl_activity
from ingestion.schemas import RelationshipRecord

logger = logging.getLogger(__name__)

# RA-relevant target ChEMBL IDs (curated from literature)
RA_TARGETS = [
    "CHEMBL1824",   # HER2/ERBB2
    "CHEMBL244",    # TNF
    "CHEMBL2103830", # JAK1
    "CHEMBL2146302", # JAK2
    "CHEMBL2146303", # JAK3
    "CHEMBL4078",   # IL6
    "CHEMBL3399910", # IL6R
    "CHEMBL325",    # IL1B
    "CHEMBL224",    # COX2/PTGS2
    "CHEMBL217",    # COX1/PTGS1
    "CHEMBL3712",   # CD20/MS4A1
    "CHEMBL3522",   # CTLA4
    "CHEMBL258",    # MTOR
    "CHEMBL1908398", # TYK2
]


async def load_ra_target_interactions(engine) -> List[RelationshipRecord]:
    """Load Drug->Target interactions for RA-relevant targets."""
    records = []
    for target_id in RA_TARGETS:
        try:
            activities = await get_chembl_activity(target_id)
            records.extend(activities)
            logger.info(f"Loaded {len(activities)} activities for target {target_id}")
        except Exception as e:
            logger.error(f"Error loading target {target_id}: {e}")
    return records
