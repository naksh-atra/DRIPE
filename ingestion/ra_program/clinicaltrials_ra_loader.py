"""
RA-focused ClinicalTrials.gov loader.
Filters trials to RA-relevant interventional studies.
"""
import logging
from typing import List
from ingestion.clinicaltrials_connector import get_clinical_trials
from ingestion.schemas import RelationshipRecord

logger = logging.getLogger(__name__)


async def load_ra_trials() -> List[Dict]:
    """Load RA-relevant clinical trials."""
    try:
        trials = get_clinical_trials("rheumatoid arthritis", max_results=100)
        logger.info(f"Loaded {len(trials)} RA trials")
        return trials
    except Exception as e:
        logger.error(f"Error loading RA trials: {e}")
        return []


def trials_to_records(trials: List[Dict], disease_cui: str = "C0003873") -> List[RelationshipRecord]:
    """Convert trial data to graph records."""
    records = []
    for trial in trials:
        nct_id = trial.get("nct_id", "")
        if not nct_id:
            continue
        records.append(RelationshipRecord(
            source_id=nct_id,
            source_type="Trial",
            target_id=disease_cui,
            target_type="Disease",
            relationship_type="TRIAL_CONDITION",
            confidence=0.7,
            source_db="clinicaltrials",
            evidence_year=trial.get("phase", "Unknown"),
        ))
    return records
