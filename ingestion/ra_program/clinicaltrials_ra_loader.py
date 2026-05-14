"""
RA-focused ClinicalTrials.gov loader.
Filters trials to RA-relevant interventional studies.
"""
import logging
from typing import List, Dict
from ingestion.clinicaltrials_connector import get_clinical_trials
from ingestion.schemas import RelationshipRecord

logger = logging.getLogger(__name__)

RA_DRUG_NAMES = [
    "methotrexate", "adalimumab", "etanercept", "infliximab", "rituximab",
    "tocilizumab", "baricitinib", "tofacitinib", "abatacept",
]


async def load_ra_trials() -> List[Dict]:
    """Load RA-relevant clinical trials for common RA drugs."""
    all_trials = []
    seen_ncts = set()
    for drug in RA_DRUG_NAMES:
        try:
            trials = await get_clinical_trials(drug)
            for t in trials:
                nct = t.get("nct_id", "")
                if nct and nct not in seen_ncts:
                    seen_ncts.add(nct)
                    all_trials.append(t)
            logger.info(f"Loaded {len(trials)} trials for {drug}")
        except Exception as e:
            logger.error(f"Error loading RA trials for {drug}: {e}")
    logger.info(f"Total unique RA trials: {len(all_trials)}")
    return all_trials


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
            evidence_year=2023,
        ))
    return records
