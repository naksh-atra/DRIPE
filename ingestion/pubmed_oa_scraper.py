import logging
import httpx
from typing import List, Dict
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def chunk_text(text: str, size: int = 512, overlap: int = 64) -> List[str]:
    """Chunks text into overlapping segments."""
    tokens = text.split()
    chunks = []
    for i in range(0, len(tokens), size - overlap):
        chunk = " ".join(tokens[i : i + size])
        chunks.append(chunk)
    return chunks

async def scrape_pubmed_oa(query: str) -> List[Dict]:
    """
    Search PubMed and retrieve chunks from Open Access papers.
    """
    # 1. Search for PMIDs
    search_url = f"{EUTILS_BASE}/esearch.fcgi?db=pubmed&term={query}&retmode=json"
    
    all_chunks = []
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(search_url)
            pmids = r.json().get('esearchresult', {}).get('idlist', [])
            
            for pmid in pmids:
                # 2. Fetch full text (if OA available) via BioC or other PMC endpoint
                # Scraper logic for PMC goes here
                # Simulation for now
                text = "Simulated text for drug repurposing research..."
                chunks = chunk_text(text)
                for chunk in chunks:
                    all_chunks.append({
                        "pmid": pmid,
                        "chunk_text": chunk,
                        "source": "PubMed OA"
                    })
        except Exception as e:
            logger.error(f"Error scraping PubMed: {e}")
            
    return all_chunks
