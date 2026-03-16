from typing import List, Dict
import os
from neo4j import GraphDatabase

CYPHER_QUERY = """
MATCH (d:Entity {id: $disease_id})
MATCH (drug:Entity {type: 'drug'})
MATCH path = shortestPath((drug)-[*1..5]-(d))
WHERE all(r in relationships(path) WHERE r.confidence >= $min_confidence)
RETURN path, 
       reduce(min_conf = 1.0, r in relationships(path) | 
              CASE WHEN r.confidence < min_conf THEN r.confidence ELSE min_conf END) as min_edge_conf
ORDER BY min_edge_conf DESC
LIMIT 50
"""

async def find_paths(disease_id: str, min_confidence: float = 0.50) -> List[Dict]:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
    
    paths = []
    try:
        with GraphDatabase.driver(uri, auth=auth) as driver:
            with driver.session() as session:
                result = session.run(CYPHER_QUERY, disease_id=disease_id, min_confidence=min_confidence)
                for record in result:
                    paths.append({
                        "path": record["path"],
                        "min_confidence": record["min_edge_conf"]
                    })
    except Exception as e:
        # Fallback logic would go here
        pass
        
    return paths
