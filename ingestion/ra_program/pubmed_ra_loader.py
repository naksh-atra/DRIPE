"""
RA-focused PubMed loader.
Searches PubMed for RA-relevant drug-disease literature.
"""
import logging
from typing import List, Dict
from ingestion.pubmed_oa_scraper import search_pubmed

logger = logging.getLogger(__name__)


RA_DRUG_KEYWORDS = [
    "methotrexate", "adalimumab", "etanercept", "infliximab", "rituximab",
    "tocilizumab", "baricitinib", "tofacitinib", "abatacept", "sulfasalazine",
    "leflunomide", "hydroxychloroquine", "certolizumab", "golimumab", "sarilumab",
    "upadacitinib", "filgotinib", "anakinra", "ixekizumab", "secukinumab",
]


def load_ra_literature(max_per_drug: int = 5) -> List[Dict]:
    """Search PubMed for RA drug literature."""
    results = []
    for drug in RA_DRUG_KEYWORDS[:10]:  # Limit to first 10 for MVP
        try:
            articles = search_pubmed(drug + " rheumatoid arthritis mechanism", max_results=max_per_drug)
            results.extend(articles)
            logger.info(f"Found {len(articles)} articles for {drug}")
        except Exception as e:
            logger.error(f"Error searching for {drug}: {e}")
    return results
