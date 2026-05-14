import logging
import httpx
from typing import List
from ingestion.schemas import RelationshipRecord

logger = logging.getLogger(__name__)

CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"

async def get_chembl_activity(target_chembl_id: str) -> List[RelationshipRecord]:
    """
    Retrieves ChEMBL activity records for a specific target.
    Filters for pChEMBL value >= 6.0 (approx. 1uM potency).
    """
    # ChEMBL API filtered query
    url = f"{CHEMBL_API_BASE}/activity?target_chembl_id={target_chembl_id}&pchembl_value__gte=6.0&format=json"
    
    logger.info(f"Fetching ChEMBL activities for target: {target_chembl_id}")
    records = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            activities = data.get('activities', [])
            logger.info(f"Found {len(activities)} activities for {target_chembl_id}")
            
            for act in activities:
                molecule_id = act.get('molecule_chembl_id')
                # Map assay type to confidence
                # B = Binding, F = Functional, A = ADME, etc.
                assay_type = act.get('assay_type', 'U')
                confidence = 0.50
                if assay_type == 'B':
                    confidence = 0.85
                elif assay_type == 'F':
                    confidence = 0.80
                
                records.append(RelationshipRecord(
                    source_id=molecule_id,
                    source_type="Drug", # In ChEMBL, these are small molecules
                    target_id=target_chembl_id,
                    target_type="Protein",
                    relationship_type="INTERACTS_WITH",
                    confidence=confidence,
                    source_db="ChEMBL",
                    pmid=str(act.get('pubmed_id')) if act.get('pubmed_id') else None,
                    evidence_year=None # ChEMBL doesn't always provide yeast directly in the activity record
                ))
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching ChEMBL data: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error in ChEMBL connector: {e}")
            
    return records
