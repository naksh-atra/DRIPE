"""Lightweight FAISS indexer using direct PubMed fetch."""
import json, requests, xml.etree.ElementTree as ET, logging, sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.vectorstore import get_vector_store
from rag.embedder import get_embedder

PM_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

DRUGS = [
    "methotrexate", "adalimumab", "etanercept", "infliximab", "rituximab",
    "tocilizumab", "baricitinib", "tofacitinib", "abatacept",
]

def fetch_abstracts(drug, max_results=3):
    r = requests.get(f"{PM_BASE}/esearch.fcgi?db=pubmed&term={drug}+rheumatoid+arthritis+mechanism&retmax={max_results}&retmode=json", timeout=30)
    pmids = r.json().get("esearchresult", {}).get("idlist", [])
    if not pmids:
        return []
    r = requests.get(f"{PM_BASE}/efetch.fcgi?db=pubmed&id={','.join(pmids)}&retmode=xml", timeout=30)
    root = ET.fromstring(r.text)
    results = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", "unknown")
        abstract = article.findtext(".//AbstractText", "")
        if abstract:
            results.append({"pmid": pmid, "abstract": abstract})
    return results

def chunk_text(text, size=200, overlap=20):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        c = " ".join(words[i:i + size])
        if len(c) > 50:
            chunks.append(c)
    return chunks

def main():
    store = get_vector_store()
    store.initialize()
    embedder = get_embedder()

    all_chunks, all_meta = [], []
    for drug in DRUGS:
        articles = fetch_abstracts(drug, 3)
        for art in articles:
            for chunk in chunk_text(art["abstract"]):
                all_chunks.append(chunk)
                all_meta.append({"pmid": art["pmid"], "chunk_text": chunk, "year": 2023, "source_type": "pubmed"})

    if not all_chunks:
        logger.warning("No chunks fetched")
        return

    logger.info(f"Embedding {len(all_chunks)} chunks...")
    embeddings = embedder.embed_batch(all_chunks)
    store.add_chunks(embeddings, all_meta)
    store.save()
    logger.info(f"Done. Total vectors: {store.count}")

if __name__ == "__main__":
    main()
