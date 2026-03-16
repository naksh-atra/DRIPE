import faiss
import sqlite3
import numpy as np
import os

class VectorStore:
    def __init__(self, index_path="faiss_index.bin", db_path="pubmed_chunks.db"):
        self.index_path = index_path
        self.db_path = db_path
        self.index = None
        self.db_conn = None

    def initialize(self, dim=128): # Dimension depends on model
        self.index = faiss.IndexFlatIP(dim)
        self.db_conn = sqlite3.connect(self.db_path)
        self._create_schema()

    def _create_schema(self):
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

    def add_chunks(self, embeddings: np.ndarray, metadata: list):
        self.index.add(embeddings)
        cursor = self.db_conn.cursor()
        for meta in metadata:
            cursor.execute("INSERT INTO chunks (pmid, chunk_text, year) VALUES (?, ?, ?)",
                           (meta['pmid'], meta['chunk_text'], meta['year']))
        self.db_conn.commit()

    def save(self):
        faiss.write_index(self.index, self.index_path)
        
    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.db_conn = sqlite3.connect(self.db_path)
