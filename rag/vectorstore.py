"""
FAISS vector store for DRIPE RAG layer.
Stores embeddings and metadata for semantic search.
"""
import faiss
import sqlite3
import numpy as np
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_INDEX_PATH = "data/faiss_index.bin"
DEFAULT_DB_PATH = "data/pubmed_chunks.db"


class VectorStore:
    """FAISS vector store with SQLite metadata."""
    
    def __init__(
        self,
        index_path: str = DEFAULT_INDEX_PATH,
        db_path: str = DEFAULT_DB_PATH,
        dimension: int = 384
    ):
        self.index_path = index_path
        self.db_path = db_path
        self.dimension = dimension
        self.index = None
        self.db_conn = None
        self._initialized = False
    
    def initialize(self, dimension: int = None):
        """Initialize or load the vector store."""
        if dimension:
            self.dimension = dimension
        
        # Create directories if needed
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Try to load existing index
        if os.path.exists(self.index_path):
            self.load()
        else:
            self._create_new()
        
        self._initialized = True
    
    def _create_new(self):
        """Create a new FAISS index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.db_conn = sqlite3.connect(self.db_path)
        self._create_schema()
        logger.info(f"Created new FAISS index (dim={self.dimension})")
    
    def _create_schema(self):
        """Create SQLite schema for metadata."""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY,
                pmid TEXT,
                chunk_text TEXT,
                year INTEGER
            )
        """)
        self.db_conn.commit()
    
    def add_chunks(self, embeddings: np.ndarray, metadata: List[Dict]):
        """Add embeddings and metadata to the store."""
        if not self._initialized:
            self.initialize()
        
        # Add to FAISS
        self.index.add(embeddings)
        
        # Add to SQLite
        cursor = self.db_conn.cursor()
        for meta in metadata:
            cursor.execute(
                "INSERT INTO chunks (pmid, chunk_text, year) VALUES (?, ?, ?)",
                (meta.get('pmid', ''), meta.get('chunk_text', ''), meta.get('year', 0))
            )
        self.db_conn.commit()
        
        logger.info(f"Added {len(metadata)} chunks to vector store")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Search for similar vectors."""
        if not self._initialized or self.index is None:
            return []
        
        # Reshape query for FAISS
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Fetch metadata
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            
            # FAISS index is 0-indexed, SQLite rowid starts at 1
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT pmid, chunk_text, year FROM chunks WHERE id = ?", (int(idx) + 1,))
            row = cursor.fetchone()
            
            if row:
                results.append({
                    "pmid": row[0],
                    "text": row[1],
                    "year": row[2],
                    "relevance_score": float(dist)
                })
        
        return results
    
    def save(self):
        """Save FAISS index to disk."""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            logger.info(f"Saved FAISS index to {self.index_path}")
    
    def load(self):
        """Load FAISS index from disk."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.db_conn = sqlite3.connect(self.db_path)
            self.dimension = self.index.d
            logger.info(f"Loaded FAISS index ({self.index.ntotal} vectors, dim={self.dimension})")
        else:
            logger.warning(f"No index found at {self.index_path}")
            self._create_new()
    
    @property
    def count(self) -> int:
        """Get number of vectors in store."""
        if self.index is None:
            return 0
        return self.index.ntotal


# Singleton instance
_store: VectorStore = None


def get_vector_store() -> VectorStore:
    """Get or create singleton vector store."""
    global _store
    if _store is None:
        _store = VectorStore()
        _store.initialize()
    return _store
