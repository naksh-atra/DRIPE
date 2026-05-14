"""
Sentence transformer embedder for DRIPE RAG layer.
Uses lightweight models for semantic search.
"""
import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Default model - lightweight and effective for semantic search
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder:
    """Wrapper for sentence-transformers embeddings."""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedder model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedder loaded successfully (dim={self.model.get_sentence_embedding_dimension()})")
        except Exception as e:
            logger.error(f"Error loading embedder: {e}")
            self.model = None
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        if self.model is None:
            return np.zeros(384, dtype=np.float32)
        
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.astype(np.float32)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of texts."""
        if self.model is None:
            return np.zeros((len(texts), 384), dtype=np.float32)
        
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        return embeddings.astype(np.float32)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self.model is None:
            return 384
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
_embedder: Embedder = None


def get_embedder() -> Embedder:
    """Get or create singleton embedder."""
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder
