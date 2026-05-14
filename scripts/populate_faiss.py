"""
Populate FAISS index with sample PubMed literature.
Simple synchronous version for testing.
"""
import requests
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict

from rag.embedder import get_embedder
from rag.vectorstore import get_vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Sample drug-disease pairs from our seed data
SAMPLE_PAIRS = [
    ("metformin", "diabetes"),
    ("aspirin", "cardiovascular disease"),
    ("ibuprofen", "inflammation"),
    ("omeprazole", "acid reflux"),
    ("atorvastatin", "hyperlipidemia"),
]


def search_pubmed(drug: str, disease: str, max_results: int = 5) -> List[Dict]:
    """Search PubMed for abstracts."""
    query = f"{drug} {disease} mechanism"
    search_url = f"{EUTILS_BASE}/esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
    
    try:
        r = requests.get(search_url, timeout=30)
        pmids = r.json().get('esearchresult', {}).get('idlist', [])
        logger.info(f"Found {len(pmids)} PMIDs for {drug} + {disease}")
    except Exception as e:
        logger.error(f"Error searching PubMed: {e}")
        return []
    
    if not pmids:
        return []
    
    # Fetch abstracts
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
                results.append({
                    "pmid": pmid,
                    "abstract": abstract
                })
        
        return results
    except Exception as e:
        logger.error(f"Error fetching abstracts: {e}")
        return []


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 20) -> List[str]:
    """Split text into chunks."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk) > 50:  # Skip tiny chunks
            chunks.append(chunk)
    
    return chunks


def populate():
    """Fetch PubMed abstracts and add to FAISS."""
    embedder = get_embedder()
    vectorstore = get_vector_store()
    
    all_chunks = []
    all_metadata = []
    
    for drug, disease in SAMPLE_PAIRS:
        logger.info(f"Fetching literature for {drug} + {disease}")
        
        # Search PubMed
        results = search_pubmed(drug, disease, max_results=3)
        
        for result in results:
            pmid = result.get("pmid", "unknown")
            text = result.get("abstract", "")
            
            if not text:
                continue
            
            # Chunk the abstract
            chunks = chunk_text(text)
            
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append({
                    "pmid": pmid,
                    "chunk_text": chunk,
                    "year": 2023  # Placeholder
                })
    
    if not all_chunks:
        logger.warning("No chunks to add")
        return
    
    # Generate embeddings
    logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
    embeddings = embedder.embed_batch(all_chunks)
    
    # Add to vector store
    vectorstore.add_chunks(embeddings, all_metadata)
    vectorstore.save()
    
    logger.info(f"Added {len(all_chunks)} chunks to FAISS index")
    logger.info(f"Total vectors in store: {vectorstore.count}")


if __name__ == "__main__":
    populate()
