import logging
from typing import List, Dict
import numpy as np
import sqlite3
import faiss
from rag.embedder import MedGemmaEmbedder

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, vectorstore, embedder: MedGemmaEmbedder):
        self.vectorstore = vectorstore
        self.embedder = embedder

    async def retrieve_context(self, drug_name: str, disease_name: str, top_k: int = 10) -> List[Dict]:
        """
        Retrieves top K semantically relevant PubMed chunks for a drug-disease pair.
        """
        query_str = f"drug {drug_name} mechanism disease {disease_name} repurposing therapeutic"
        query_embedding = self.embedder.embed_text(query_str).numpy().astype('float32')
        
        # Search FAISS
        distances, indices = self.vectorstore.index.search(query_embedding, top_k)
        
        results = []
        # Connect to metadata DB
        conn = sqlite3.connect(self.vectorstore.db_path)
        cursor = conn.cursor()
        
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1: continue
            
            # FAISS index is 0-indexed, but sqlite rowid might start at 1
            cursor.execute("SELECT pmid, chunk_text, year FROM chunks WHERE rowid = ?", (int(idx) + 1,))
            row = cursor.fetchone()
            if row:
                results.append({
                    "pmid": row[0],
                    "text": row[1],
                    "year": row[2],
                    "relevance_score": float(dist)
                })
        
        conn.close()
        return results
