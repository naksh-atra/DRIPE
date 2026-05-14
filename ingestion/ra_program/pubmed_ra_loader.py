"""
RA-focused PubMed loader.
Searches PubMed for RA-relevant drug-disease literature.
"""
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

RA_DRUG_QUERIES = [
    "methotrexate rheumatoid arthritis mechanism",
    "adalimumab rheumatoid arthritis mechanism",
    "etanercept rheumatoid arthritis mechanism",
    "infliximab rheumatoid arthritis mechanism",
    "rituximab rheumatoid arthritis mechanism",
    "tocilizumab rheumatoid arthritis mechanism",
    "baricitinib rheumatoid arthritis",
    "tofacitinib rheumatoid arthritis",
    "abatacept rheumatoid arthritis",
    "sulfasalazine rheumatoid arthritis",
]


def search_pubmed(query: str, max_results: int = 5) -> List[Dict]:
    """Search PubMed for abstracts matching a query."""
    search_url = f"{EUTILS_BASE}/esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
    try:
        r = requests.get(search_url, timeout=30)
        pmids = r.json().get('esearchresult', {}).get('idlist', [])
    except Exception as e:
        logger.error(f"PubMed search error: {e}")
        return []

    if not pmids:
        return []

    fetch_url = f"{EUTILS_BASE}/efetch.fcgi?db=pubmed&id={','.join(pmids)}&retmode=xml"
    try:
        r = requests.get(fetch_url, timeout=30)
        root = ET.fromstring(r.text)
        results = []
        for article in root.findall('.//PubmedArticle'):
            pmid = article.find('.//PMID').text if article.find('.//PMID') is not None else "unknown"
            abstract_elem = article.find('.//AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else ""
            if abstract:
                results.append({"pmid": pmid, "abstract": abstract})
        return results
    except Exception as e:
        logger.error(f"PubMed fetch error: {e}")
        return []


def load_ra_literature(max_per_query: int = 3) -> List[Dict]:
    """Search PubMed for RA drug literature."""
    results = []
    for query in RA_DRUG_QUERIES[:10]:
        try:
            articles = search_pubmed(query, max_results=max_per_query)
            results.extend(articles)
            logger.info(f"Found {len(articles)} articles for {query.split()[0]}")
        except Exception as e:
            logger.error(f"Error for query '{query}': {e}")
    return results
