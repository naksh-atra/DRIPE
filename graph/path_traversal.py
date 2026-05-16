from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PathTraversal:
    def __init__(self, engine=None):
        self.engine = engine

    async def get_drug_disease_paths(self, disease_id: str, max_depth: int = 3) -> List[Dict]:
        """
        Finds paths from any Drug node to the target Disease node in Neo4j.
        Returns a list of paths with node/edge details.
        """
        if not self.engine or not self.engine.is_connected():
            logger.warning("PathTraversal: No connected GraphEngine provided. Returning empty paths.")
            return []

        # Cypher for variable-length path discovery: Drug -> (Protein/Gene) -> Disease
        # We query for paths where the destination has entity_id = disease_id
        # Note: depth must be literal in pattern, not parameterized
        cypher = f"""
        MATCH p = (drug:Entity {{entity_type: 'Drug'}})-[:BIOREL*1..{max_depth}]-(disease:Entity {{entity_id: $did}})
        WHERE drug.name IS NOT NULL AND drug.name <> ''
        RETURN 
            drug.entity_id AS drug_id,
            drug.name AS drug_name,
            [n in nodes(p) | {{id: n.entity_id, type: n.entity_type}}] AS path_nodes,
            [r in relationships(p) | {{type: r.type, confidence: r.confidence}}] AS path_edges
        ORDER BY reduce(conf = 1.0, r IN relationships(p) | conf * COALESCE(r.confidence, 0.5)) DESC
        LIMIT 50
        """
        try:
            results = self.engine.run_cypher(cypher, {"did": disease_id})
            
            # Format results into a common schema
            formatted_paths = []
            for res in results:
                formatted_paths.append({
                    "drug_id": res["drug_id"],
                    "drug_name": res.get("drug_name", ""),
                    "nodes": res["path_nodes"],
                    "edges": res["path_edges"],
                    "path_confidence": sum(e["confidence"] for e in res["path_edges"]) / len(res["path_edges"]) if res["path_edges"] else 0
                })
                
            return formatted_paths
        except Exception as e:
            logger.error(f"Error during path traversal: {e}")
            return []
