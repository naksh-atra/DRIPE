import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

OPENFDA_BASE = "https://api.fda.gov/drug/event.json"

async def get_safety_profile(drug_name: str) -> Dict[str, Any]:
    """
    Retrieves adverse event profile from OpenFDA.
    """
    query = f'search=patient.drug.medicinalproduct:"{drug_name}"&count=patient.reaction.reactionmeddrapt.exact'
    url = f"{OPENFDA_BASE}?{query}&limit=20"
    
    profile = {
        "drug_name": drug_name,
        "adverse_events": [],
        "demographics": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                profile["adverse_events"] = data.get("results", [])
            
            # Fetch demographic stats separately or include in query
            # ...
        except Exception as e:
            logger.error(f"Error fetching OpenFDA data for {drug_name}: {e}")
            
    return profile
