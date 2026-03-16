import logging
import httpx
from typing import List
from ingestion.schemas import RelationshipRecord

logger = logging.getLogger(__name__)

CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data"

async def get_chembl_activity(target_id: str) -> List[RelationshipRecord]:
    """
    Retrieves ChEMBL activity records for a target.
    Filters for pChEMBL >= 6.0.
    """
    url = f"{CHEMBL_API_BASE}/activity?target_chembl_id={target_id}&pchembl_value__gte=6.0&format=json"
    
    records = []
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            for act in data.get('activities', []):
                # Mapping logic here
                assay_type = act.get('assay_type', 'U')
                confidence = 0.60
                if assay_type == 'B': confidence = 0.85
                elif assay_type == 'F': confidence = 0.80
                
                records.append(RelationshipRecord(
                    source_id=act.get('molecule_chembl_id'),
                    source_type="drug",
                    target_id=target_id,
                    target_type="protein",
                    relationship_type="interacts_with",
                    confidence=confidence,
                    source_db="ChEMBL",
                    pmid=act.get('pubmed_id')
                ))
        except Exception as e:
            logger.error(f"Error fetching ChEMBL data: {e}")
            
    return records
