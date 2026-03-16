import logging
import httpx
from typing import List, Dict

logger = logging.getLogger(__name__)

CT_API_BASE = "https://clinicaltrials.gov/api/v2/studies"

async def get_clinical_trials(drug_name: str) -> List[Dict]:
    """
    Retrieves clinical trials for a drug.
    """
    query = f"query.intr={drug_name}"
    url = f"{CT_API_BASE}?{query}&pageSize=50"
    
    trials = []
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                for study in data.get("studies", []):
                    info = study.get("protocolSection", {})
                    trials.append({
                        "nct_id": info.get("identificationModule", {}).get("nctId"),
                        "condition": info.get("conditionsModule", {}).get("conditions", []),
                        "phase": info.get("designModule", {}).get("phases", []),
                        "status": info.get("statusModule", {}).get("overallStatus"),
                        "outcome": info.get("outcomesModule", {}).get("primaryOutcomes", [])
                    })
        except Exception as e:
            logger.error(f"Error fetching ClinicalTrials.gov data for {drug_name}: {e}")
            
    return trials
