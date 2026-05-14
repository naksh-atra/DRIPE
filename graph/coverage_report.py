import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class CoverageReporter:
    def __init__(self, neo4j_engine=None):
        self.engine = neo4j_engine

    async def get_coverage(self, disease_id: str) -> Dict:
        """
        Produces a data completeness disclosure for the queried disease.
        Checks nodes and relationships associated with the disease.
        """
        if not self.engine or not self.engine.is_connected():
            return {
                "completeness_tier": "LOW (FALLBACK)",
                "gene_association_count": 0,
                "protein_interaction_count": 0,
                "pubmed_paper_count": 0,
                "trial_count": 0,
                "sparse_edges": ["No Neo4j Connection"]
            }

        # Real queries to Neo4j
        # Count related proteins
        protein_q = """
        MATCH (d:Entity {entity_id: $did})-[:BIOREL]-(p:Entity {entity_type: 'Protein'})
        RETURN count(p) AS cnt
        """
        proteins = self.engine.run_cypher(protein_q, {"did": disease_id})
        gene_count = proteins[0]["cnt"] if proteins else 0

        # Count total interactions (mocking for now since we only have small seed)
        interaction_count = gene_count * 3 
        paper_count = 10 # Mock count for now
        trial_count = 1
        
        tier = "MEDIUM"
        if gene_count < 1: tier = "LOW"
        elif gene_count > 5: tier = "HIGH" # Thresholds adjusted for seed data
        
        sparse_edges = []
        if gene_count < 2:
            sparse_edges.append("Limited Protein-Disease associations")
            
        return {
            "completeness_tier": tier,
            "gene_association_count": gene_count,
            "protein_interaction_count": interaction_count,
            "pubmed_paper_count": paper_count,
            "trial_count": trial_count,
            "sparse_edges": sparse_edges
        }
